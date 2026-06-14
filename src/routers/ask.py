import json
import logging
import time
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.dependencies import CacheDep, EmbeddingsDep, OllamaDep, OpenSearchDep, LangfuseDep
from src.schemas.api.ask import AskRequest, AskResponse
from langfuse import observe

logger = logging.getLogger(__name__)

# Two separate routers - one for regular ask, one for streaming
ask_router = APIRouter(tags=["ask"])
stream_router = APIRouter(tags=["stream"])

# @observe(as_type="span", name="trace_prepare_chunks")
async def _prepare_chunks_and_sources(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    langfuse: LangfuseDep,
) -> tuple[List[Dict], List[str], List[str]]:
    """Retrieve and prepare chunks for RAG with clean tracing."""
    with langfuse.start_as_current_observation(
        as_type="span", 
        name="trace_prepare_chunks",
        input = {"user_query": request.query})  as root_span:
        # Handle embeddings for hybrid search
        query_embedding = None
        if request.use_hybrid:
            query_embedding = await _get_query_embedding(embeddings_service, request.query, langfuse)
        chunks, sources_sets, arxiv_ids = _execute_search_and_process(request, opensearch_client, langfuse, query_embedding)
    return chunks, sources_sets, arxiv_ids

# @observe(as_type="span", name="trace_embedding")
async def _get_query_embedding(embeddings_service: EmbeddingsDep, query: str, langfuse: LangfuseDep) -> List[float]:
    """Get query embedding from embeddings service."""
    with langfuse.start_as_current_observation(
        as_type="span", 
        name="trace_embedding",
        input = {"user_query": query,"model":embeddings_service.model}) as span:
        try:
            query_embedding = await embeddings_service.embed_query(query)
            span.update(output={"success":True,"query_embedding": query_embedding,"dimensions":len(query_embedding)})    
            logger.info("Generated query embedding for hybrid search")
            return query_embedding
        except Exception as e:
            logger.warning(f"Failed to generate embeddings, falling back to BM25: {e}")
            span.update(output={"success":False,"error": f"Failed to generate embeddings, falling back to BM25: {e}"})
    return None

# @observe(as_type="span", name="trace_search")
def _execute_search_and_process(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    langfuse: LangfuseDep,
    query_embedding: List[float],
    ) -> tuple[List[Dict[str,Any]], List[str], List[str]]:
    with langfuse.start_as_current_observation(
            as_type="span", 
            name="trace_search",
            input = {"user_query": request.query}) as span:
        """Execute search with tracing."""
        search_results = opensearch_client.search_unified(
            query=request.query,
            query_embedding=query_embedding,
            size=request.top_k,
            from_=0,
            categories=request.categories,
            use_hybrid=request.use_hybrid and query_embedding is not None,
            min_score=0.0,
        )

        # Extract essential data for LLM
        chunks = []
        arxiv_ids = []
        sources_set = set()

        for hit in search_results.get("hits", []):
            arxiv_id = hit.get("arxiv_id", "")

            # Minimal chunk data for LLM
            chunks.append(
                {
                    "arxiv_id": arxiv_id,
                    "chunk_text": hit.get("chunk_text", hit.get("abstract", "")),
                }
            )

            if arxiv_id:
                arxiv_ids.append(arxiv_id)
                arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
                sources_set.add(f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf")

        span.update(
            output={
                "chunks_count": len(chunks),
                "arxiv_ids": arxiv_ids,
                "total_hits": search_results.get("total", 0),
                "sources": list(sources_set)
            }
        )
        # End search span with essential metadata
    return chunks, list(sources_set), arxiv_ids


@ask_router.post("/ask", response_model=AskResponse)
# @observe(name="trace_ask_question",)  # 声明整个请求的根节点 (Trace)
async def ask_question(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    ollama_client: OllamaDep,
    cache_client: CacheDep,
    langfuse: LangfuseDep,
) -> AskResponse:
    """Clean RAG endpoint with essential tracing and exact match caching."""

    #注入根节点的元数据
    with langfuse.start_as_current_observation(
        as_type="span", 
        name="trace_ask_question",
        input = {"user_query": request.query}) as root_span:
        try:
            # Check exact cache first
            if cache_client:
                try:
                    cached_response = await cache_client.find_cached_response(request)
                    if cached_response:
                        root_span.update(output={"response": cached_response,'stored_in_cache':False,'use_cache': True})
                        logger.info("Returning cached response for exact query match")
                        return cached_response
                except Exception as e:
                    # langfuse_context.update_current_span(
                    #     level="WARNING",
                    #     status_message=f"Cache check failed due to: {str(e)}"
                    # )
                    logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

            chunks, sources, _ = await _prepare_chunks_and_sources(
                request, opensearch_client, embeddings_service, langfuse
            )

            if not chunks:
                response = AskResponse(
                    query=request.query,
                    answer="I couldn't find any relevant information in the papers to answer your question.",
                    sources=[],
                    chunks_used=0,
                    search_mode="bm25" if not request.use_hybrid else "hybrid",
                )
                return response

            # 构建 Prompt (直接调用抽离后的装饰器函数，自动成为 Trace 的子节点)
            final_prompt = _build_rag_prompt(request.query, chunks, langfuse)

            # 生成答案 (调用异步 Generation 装饰器函数，自动成为子节点中的大模型观测)
            answer = await _generate_llm_answer(ollama_client, request.query, chunks, request.model, langfuse)

            # Prepare response
            response = AskResponse(
                query=request.query,
                answer=answer,
                sources=sources,
                chunks_used=len(chunks),
                search_mode="bm25" if not request.use_hybrid else "hybrid",
            )

            # Store response in exact match cache
            if cache_client:
                try:
                    await cache_client.store_response(request, response)
                except Exception as e:
                    logger.warning(f"Failed to store response in cache: {e}")
            root_span.update(output={"response": response,'stored_in_cache': True if cache_client else False,'use_cache': False})
            return response

        except Exception as e:
            root_span.update(output={"response": f"Error processing request: {e}",'stored_in_cache': False,'use_cache': False})
            logger.error(f"Error processing request: {e}")
            # 如果最外层抛出了 500 异常，@observe 会自动把这个 Trace 标红并记录崩溃堆栈
            raise HTTPException(status_code=500, detail=str(e))

# 抽离 Prompt 构建步骤（类型为普通的 span）
# @observe(as_type="span", name="trace_prompt_construction")
def _build_rag_prompt(query: str, chunks: List[Dict[str, Any]], langfuse: LangfuseDep) -> str:
    """构建 RAG 提示词并自动追踪"""
    from src.services.ollama.prompts import RAGPromptBuilder
    prompt_builder = RAGPromptBuilder()
    with langfuse.start_as_current_observation(
        as_type="span", 
        name="trace_prompt_construction",
        input = {"user_query": query,"chunks":chunks} ) as span:
        try:
            prompt_data = prompt_builder.create_structured_prompt(query, chunks)
            final_prompt = prompt_data["prompt"]
        except Exception:
            final_prompt = prompt_builder.create_rag_prompt(query, chunks)
        span.update(output={"final_prompt": final_prompt})
    return final_prompt

# 抽离大模型回答生成（类型为 generation）
# @observe(as_type="generation", name="trace_generation")
async def _generate_llm_answer(ollama_client: Any, query: str, chunks: List[Dict[str, Any]], model: str, langfuse: LangfuseDep) -> str:
    """调用 Ollama 生成回答并自动追踪模型生成指标"""
    # 动态通知 Langfuse 当前使用的是哪个本地模型（例如 qwen3.5:35b-a3b）
    with langfuse.start_as_current_observation(
        as_type="generation", 
        name="trace_generation",
        input = {"user_query": query,"model":model,"chunks":chunks} )  as gen:
        rag_response = await ollama_client.generate_rag_answer(query=query, chunks=chunks, model=model)
        answer = rag_response.get("answer", "Unable to generate answer")
        gen.update(output={"success": True,"answer": answer})
    return answer


@stream_router.post("/stream")
# @observe(name="trace_ask_question_stream")
async def ask_question_stream(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    ollama_client: OllamaDep,
    cache_client: CacheDep,
    langfuse: LangfuseDep,
) -> StreamingResponse:
    """Clean streaming RAG endpoint."""

    async def generate_stream():
        with langfuse.start_as_current_observation(
            as_type="span",
            name="trace_streaming",
            input={"query": request.query, "model": request.model}
        ) as root_span:
            start_time = time.time()
            try:
                # Check exact cache first
                if cache_client:
                    with langfuse.start_as_current_observation(
                        as_type="span",
                        name="trace_cache_check",
                        input={"user_query": request.query}
                    ) as cache_span:
                        try:
                            cached_response = await cache_client.find_cached_response(request)
                            if cached_response:
                                logger.info("Returning cached response for exact streaming query match")
                                cache_span.update(output={"cached": True, "hit": True})

                                metadata_response = {
                                    "sources": cached_response.sources,
                                    "chunks_used": cached_response.chunks_used,
                                    "search_mode": cached_response.search_mode,
                                }
                                yield f"data: {json.dumps(metadata_response)}\n\n"

                                for chunk in cached_response.answer.split():
                                    yield f"data: {json.dumps({'chunk': chunk + ' '})}\n\n"

                                yield f"data: {json.dumps({'answer': cached_response.answer, 'done': True})}\n\n"
                                return
                            else:
                                cache_span.update(output={"cached": True, "hit": False})
                        except Exception as e:
                            cache_span.update(output={"cached": False, "error": str(e)})
                            logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

                # Retrieve chunks
                chunks, sources, _ = await _prepare_chunks_and_sources(
                    request, opensearch_client, embeddings_service, langfuse
                )

                if not chunks:
                    root_span.update(output={"success": False, "error": "No chunks found"})
                    yield f"data: {json.dumps({'answer': 'No relevant information found.', 'sources': [], 'done': True})}\n\n"
                    return

                # Send metadata first
                search_mode = "bm25" if not request.use_hybrid else "hybrid"
                metadata_response = {"sources": sources, "chunks_used": len(chunks), "search_mode": search_mode}
                yield f"data: {json.dumps(metadata_response)}\n\n"

                # Build prompt
                final_prompt = _build_rag_prompt(request.query, chunks, langfuse)

                # Stream generation
                full_response = ""
                async for chunk_data in _generate_llm_answer_stream(ollama_client, request.query, chunks, request.model, langfuse):
                    yield chunk_data

                    if "chunk" in chunk_data:
                        try:
                            parsed = json.loads(chunk_data.replace("data: ", "").strip())
                            if "chunk" in parsed:
                                full_response += parsed["chunk"]
                        except Exception:
                            pass

                # Store response in exact match cache
                if cache_client and full_response:
                    with langfuse.start_as_current_observation(
                        as_type="span",
                        name="trace_cache_store",
                        input={"user_query": request.query}
                    ) as cache_store_span:
                        try:
                            response_to_cache = AskResponse(
                                query=request.query,
                                answer=full_response,
                                sources=sources,
                                chunks_used=len(chunks),
                                search_mode=search_mode,
                            )
                            await cache_client.store_response(request, response_to_cache)
                            cache_store_span.update(output={"success": True})
                        except Exception as e:
                            cache_store_span.update(output={"success": False, "error": str(e)})
                            logger.warning(f"Failed to store streaming response in cache: {e}")

                root_span.update(output={"success": True, "answer_length": len(full_response)})

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                root_span.update(output={"success": False, "error": str(e)})
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(), media_type="text/plain", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# @observe(as_type="generation", name="trace_generate_llm_answer_stream")
async def _generate_llm_answer_stream(
    ollama_client: Any, query: str, chunks: List[Dict[str, Any]], model: str, langfuse: LangfuseDep
) -> StreamingResponse:
    """调用 Ollama 生成回答并自动追踪模型生成指标"""
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="trace_generation_stream",
        input={"user_query": query, "model": model, "chunks": chunks}
    ) as gen:
        accumulated_text = ""
        async for chunk in ollama_client.generate_rag_answer_stream(
            query=query, chunks=chunks, model=model
        ):
            if chunk.get("response"):
                text_chunk = chunk["response"]
                accumulated_text += text_chunk
                yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"

            if chunk.get("done", False):
                yield f"data: {json.dumps({'answer': accumulated_text, 'done': True})}\n\n"
                break
        gen.update(output={"success": True, "answer": accumulated_text})
