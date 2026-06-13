# src根目录

- `dependencies.py`：模块定义了 FastAPI 依赖注入（Dependency Injection） ，用于在整个应用中提供可复用的服务实例。服务在应用启动时创建，请求结束时销毁，避免重复创建对象，提高性能。
- `radio_app.py`模块：构建了一个 Gradio 网页界面应用 ，为 ArXiv-RAG-System 提供可视化的交互式问答界面。
- `main.py`模块：FastAPI 应用的入口模块 ，函数负责应用初始化、服务配置和路由注册。
   - 定义`lifespan`函数：管理应用启动和关闭时的资源初始化/清理。
   - 将各服务实例存入 app.state 供依赖注入使用。
   - 路由注册：挂载所有 API 路由到 /api/v1 前缀
      ```
      app.include_router(ping.router, prefix="/api/v1")
      app.include_router(hybrid_search.router, prefix="/api/v1")
      app.include_router(ask.ask_router, prefix="/api/v1")
      app.include_router(ask.stream_router, prefix="/api/v1")
      app.include_router(agentic_ask.router, prefix="/api/v1")
      ```

##  routers包

routers包里面自定义了FastAPI路由模块，负责API各个服务端点。
- `ping.py`模块提供简单的健康检查端点，用于验证服务是否正常运行。终端检测及返回结果如下：
   ```
   curl http://localhost:8000/api/v1/health
   ```
   ```
   {"status":"ok","version":"0.1.0","environment":"development","service_name":"rag-api","services":{"database":{"status":"healthy","message":"Connected successfully"},"opensearch":{"status":"healthy","message":"Index 'arxiv-papers-chunks' with 1341 documents"},"ollama":{"status":"healthy","message":"Ollama service is running"}}}
   ```
- `hybrid_search.py`模块提供文档搜索功能，提供BM25 关键词搜索、向量相似度搜索、混合搜索（BM25 + 向量），支持按 arXiv 类别过滤，可以用来调试搜索效果。
   ```
   curl -X POST "http://localhost:8000/api/v1/hybrid-search/" \
   -H "Content-Type: application/json" \
   -d '{
      "query": "transformer architecture",
      "size": 10,
      "use_hybrid": true,
      "categories": ["cs.AI", "cs.LG"],
      "latest_papers": false,
      "min_score": 0.0
   }'
   ```
- `ask.py`模块提供完整的RAG问答功能。通过示例化RAGTracer对象， 使用Langfuse，实现对RAG流程各阶段的追踪和监控。通过结合redis库创建缓存机制，提升问答速率。
   - POST /api/v1/ask - 标准问答（完整响应）
   - POST /api/v1/stream - 流式问答（实时响应）
   ```
   curl -X POST "http://localhost:8000/api/v1/ask" \
   -H "Content-Type: application/json" \
   -d '{"query": "请为我介绍一下基于koopman算子理论的adakoop算法", "top_k": 3}' \
   | jq .
   ``` 

## schemas库

提供了数据模型定义文件

### api包

- `health.py`模块：为健康检查端点提供标准化的响应格式，包含：整体状态、版本信息、各依赖服务的详细状态。
- `ask.py`模块：RAG 问答 API 的请求/响应数据模型定义模块 ，规范了问答、反馈等接口的数据结构。
- `search.py`模块：搜索 API 的数据模型定义模块 ，为文档搜索端点提供标准化的请求（支持多种搜索模式（BM25、向量、混合）的灵活配置）和响应数据结构。