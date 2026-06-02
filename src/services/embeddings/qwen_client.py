import sys
from pathlib import Path
import asyncio

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import List

import httpx
from src.schemas.embeddings.ollama import OllamaEmbeddingRequest, OllamaEmbeddingResponse

logger = logging.getLogger(__name__)


class QwenEmbeddingsClient:
    """Client for Ollama Qwen embeddings.

    Uses Qwen3-Embedding-0.6B model running locally via Ollama.
    Documentation: https://ollama.com/library/qwen3-embedding
    """

    def __init__(self, base_url: str = "http://ollama:11434", model: str = "qwen3-embedding:0.6b", api_key: str = None):
        """Initialize Qwen embeddings client.

        :param base_url: Ollama API base URL
        :param model: Model name to use for embeddings
        """
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"Qwen embeddings client initialized with model: {model}")

    async def embed_passages(self, texts: List[str], batch_size: int = 2) -> List[List[float]]:
        """Embed text passages for indexing.

        :param texts: List of text passages to embed
        :param batch_size: Number of texts to process in each batch (Ollama processes one at a time)
        :returns: List of embedding vectors
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = await self._embed_single(text)
                embeddings.append(embedding)

                if (i + 1) % batch_size == 0:
                    logger.debug(f"Embedded {i + 1}/{len(texts)} passages")

            except httpx.HTTPError as e:
                logger.error(f"kang99 Error embedding passage {i}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in embed_passages: {e}")
                raise

        logger.info(f"Successfully embedded {len(texts)} passages")
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query.

        :param query: Query text to embed
        :returns: Embedding vector for the query
        """
        try:
            embedding = await self._embed_single(query)
            logger.debug(f"Embedded query: '{query[:50]}...'")
            return embedding

        except httpx.HTTPError as e:
            logger.error(f"Error embedding query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_query: {e}")
            raise

    async def _embed_single(self, text: str) -> List[float]:
        """Embed a single text using Ollama API.

        :param text: Text to embed
        :returns: Embedding vector
        """
        request_data = OllamaEmbeddingRequest(model=self.model, input=text)

        response = await self.client.post(
            f"{self.base_url}/api/embed",
            json=request_data.model_dump(),
        )
        response.raise_for_status()
        result = OllamaEmbeddingResponse(embedding=response.json()["embeddings"][0])
        return result.embedding

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

if __name__ == "__main__":
    client = QwenEmbeddingsClient()
    embedding = asyncio.run(client.embed_query("你好"))
    print(len(embedding))