# src 目录文档树

```
src/
├── main.py                          # FastAPI 应用主入口
├── gradio_app.py                    # Gradio UI 应用
├── config.py                        # 配置管理（Pydantic Settings）
├── database.py                       # 数据库连接管理
├── dependencies.py                  # 依赖注入
├── exceptions.py                    # 自定义异常定义
├── middlewares.py                    # 中间件
│
├── config.py                        # ✅ 主配置文件（根级别）
│
├── [schemas/]                       # 📋 数据模型/Schema 定义
│   ├── __init__.py
│   ├── arxiv/
│   │   ├── __init__.py
│   │   └── paper.py                # ArxivPaper 模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ask.py                  # Agentic Ask 请求/响应模型
│   │   ├── health.py               # 健康检查模型
│   │   └── search.py               # 搜索请求/响应模型
│   ├── common/
│   │   └── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── config.py               # 数据库配置模型
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── jina.py                 # Jina 嵌入模型
│   ├── indexing/
│   │   ├── __init__.py
│   │   └── models.py               # 索引数据模型
│   ├── ollama.py                    # Ollama 模型
│   ├── pdf_parser/
│   │   ├── __init__.py
│   │   └── models.py               # PDF 解析结果模型
│   └── telegram/
│       └── __init__.py
│
├── [models/]                        # 📦 数据模型（数据库实体）
│   ├── __init__.py
│   └── paper.py                    # Paper 数据库模型
│
├── [db/]                            # 🗄️ 数据库层
│   ├── __init__.py
│   ├── factory.py                  # 数据库工厂
│   └── interfaces/
│       ├── __init__.py
│       ├── base.py                 # 数据库接口基类
│       └── postgresql.py           # PostgreSQL 实现
│
├── [repositories/]                  # 🗃️ 数据访问层
│   ├── __init__.py
│   └── paper.py                    # Paper 仓储实现
│
├── [routers/]                       # 🚏 API 路由
│   ├── __init__.py
│   ├── agentic_ask.py              # Agentic RAG 问答路由
│   ├── ask.py                      # 简单问答路由
│   ├── hybrid_search.py            # 混合搜索路由
│   └── ping.py                     # 健康检查路由
│
└── [services/]                      # 🔧 业务服务层
    ├── __init__.py
    ├── arxiv/
    │   ├── __init__.py
    │   ├── client.py               # ArXiv API 客户端
    │   └── factory.py              # ArXiv 客户端工厂
    ├── cache/
    │   ├── __init__.py
    │   ├── client.py               # 缓存客户端
    │   └── factory.py              # 缓存工厂
    ├── embeddings/
    │   ├── __init__.py
    │   ├── factory.py              # 嵌入服务工厂
    │   └── jina_client.py          # Jina 嵌入客户端
    ├── indexing/
    │   ├── __init__.py
    │   ├── factory.py              # 索引服务工厂
    │   ├── hybrid_indexer.py       # 混合索引器
    │   └── text_chunker.py         # 文本分块器
    ├── langfuse/
    │   ├── __init__.py
    │   ├── client.py               # Langfuse 追踪客户端
    │   ├── factory.py              # Langfuse 工厂
    │   └── tracer.py               # 追踪器
    ├── metadata_fetcher.py         # 元数据获取服务
    ├── ollama/
    │   ├── __init__.py
    │   ├── client.py               # Ollama LLM 客户端
    │   ├── factory.py              # Ollama 工厂
    │   ├── prompts.py              # 提示词管理
    │   └── prompts/
    │       └── rag_system.txt      # RAG 系统提示词模板
    ├── opensearch/
    │   ├── __init__.py
    │   ├── client.py               # OpenSearch 客户端
    │   ├── factory.py              # OpenSearch 工厂
    │   ├── index_config_hybrid.py  # 混合索引配置
    │   └── query_builder.py        # 查询构建器
    ├── pdf_parser/
    │   ├── __init__.py
    │   ├── docling.py              # Docling PDF 解析器
    │   ├── factory.py              # PDF 解析器工厂
    │   └── parser.py               # PDF 解析器基类
    ├── telegram/
    │   ├── __init__.py
    │   ├── bot.py                  # Telegram Bot
    │   └── factory.py              # Telegram 工厂
    └── agents/                      # 🤖 Agent 相关服务
        ├── __init__.py
        ├── agentic_rag.py          # Agentic RAG 核心逻辑
        ├── config.py               # Agent 配置
        ├── context.py              # 上下文管理
        ├── factory.py              # Agent 工厂
        ├── models.py               # Agent 数据模型
        ├── prompts.py              # Agent 提示词
        ├── state.py                # Agent 状态管理
        ├── tools.py                # Agent 工具定义
        └── nodes/                   # 🔀 Agent 节点
            ├── __init__.py
            ├── generate_answer_node.py  # 生成答案节点
            ├── grade_documents_node.py  # 文档评分节点
            ├── guardrail_node.py        # 安全护栏节点
            ├── out_of_scope_node.py     # 范围外查询节点
            ├── retrieve_node.py         # 检索节点
            ├── rewrite_query_node.py    # 重写查询节点
            └── utils.py                 # 节点工具函数
```

---

## 目录架构说明

| 目录 | 职责 | 关键文件 |
|------|------|---------|
| **schemas/** | Pydantic 数据模型 | `paper.py`, `ask.py`, `search.py` |
| **models/** | SQLAlchemy ORM 模型 | `paper.py` |
| **db/** | 数据库抽象层 | `postgresql.py`, `factory.py` |
| **repositories/** | 数据访问仓储模式 | `paper.py` |
| **routers/** | FastAPI 路由端点 | `ask.py`, `hybrid_search.py` |
| **services/** | 核心业务逻辑服务 | 各个子目录 |
| **services/arxiv/** | arXiv API 集成 | `client.py` |
| **services/pdf_parser/** | PDF 解析 | `docling.py` |
| **services/opensearch/** | 搜索引擎 | `client.py`, `query_builder.py` |
| **services/agents/** | Agentic RAG | `agentic_rag.py`, `nodes/*` |

---

## 层级依赖关系

```
routers/          (API 层)
    ↓
services/         (业务逻辑层)
    ↓
repositories/     (数据访问层)
    ↓
db/ + models/     (数据库层)
    ↓
schemas/          (数据模型层)
```
