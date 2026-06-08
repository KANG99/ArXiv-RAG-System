## Docker Compose 服务架构

### 1. 核心服务

| 服务名 | 镜像 | 容器名 | 端口 | 作用 |
|--------|------|--------|------|------|
| **api** | 自定义构建 (`.`) | rag-api | 8000 | 主 API 服务，提供 RAG 接口 |
| **postgres** | postgres:17 | rag-postgres | 5432 | 主数据库，存储应用数据 |
| **redis** | redis:7 | rag-redis | 6379 | 缓存服务 |
| **ollama** | ollama/ollama:0.24.0 | rag-ollama | 11434 | 本地大语言模型服务 |

ollama模型使用：llama3.2:1b

---

### 2. 搜索与检索

| 服务名 | 镜像 | 容器名 | 端口 | 作用 |
|--------|------|--------|------|------|
| **opensearch** | opensearchproject/opensearch:3.6.0 | rag-opensearch | 9200, 9600 | 向量数据库，存储论文向量嵌入 |
| **opensearch-dashboards** | opensearchproject/opensearch-dashboards:3.6.0 | rag-dashboards | 5601 | OpenSearch 可视化管理界面 |

---

### 3. 工作流调度

| 服务名 | 镜像 | 容器名 | 端口 | 作用 |
|--------|------|--------|------|------|
| **airflow** | 自定义构建 (`./airflow`) | rag-airflow | 8080 | Airflow 工作流调度器，定期抓取 ArXiv 论文 |

airflow版本号：3.2.0

---

### 4. LLM 可观测性（Langfuse）

| 服务名 | 镜像 | 容器名 | 端口 | 作用 |
|--------|------|--------|------|------|
| **langfuse-web** | docker.io/langfuse/langfuse:3 | rag-langfuse-web | 3001 | Langfuse 可视化界面，追踪 LLM 调用 |
| **langfuse-worker** | docker.io/langfuse/langfuse-worker:3 | rag-langfuse-worker | 3030 | Langfuse 工作器，处理异步任务 |
| **langfuse-postgres** | postgres:17 | rag-langfuse-postgres | 5433 | Langfuse 专用数据库 |
| **langfuse-redis** | docker.io/redis:7 | rag-langfuse-redis | 6380 | Langfuse 专用缓存 |
| **langfuse-minio** | docker.io/minio/minio | rag-langfuse-minio | 9090, 9091 | Langfuse 专用对象存储 |
| **clickhouse** | clickhouse/clickhouse-server:24.8-alpine | rag-clickhouse | - | Langfuse 分析数据库 |

---

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    ArXiv-RAG-System                        │
├─────────────────────────────────────────────────────────────┤
│  API (8000)  ←→  Redis  ←→  PostgreSQL  ←→  Airflow(8080) │
│       ↓                                                    │
│  OpenSearch(9200)  ←→  Ollama(11434)                      │
│       ↓                                                    │
│  OpenSearch Dashboards(5601)                               │
├─────────────────────────────────────────────────────────────┤
│                    Langfuse 可观测性                        │
│  Langfuse Web(3001) ←→ Worker(3030) ←→ ClickHouse         │
│                      ←→ Postgres ←→ Redis ←→ MinIO        │
└─────────────────────────────────────────────────────────────┘
```

### 网络配置

所有服务连接到自定义网络 `rag-network`，实现服务间隔离通信。

### 数据持久化

| 卷名 | 用途 |
|------|------|
| postgres_data | PostgreSQL 主数据库数据 |
| opensearch_data | OpenSearch 向量数据 |
| ollama_data | Ollama 模型数据 |
| redis_data | Redis 缓存数据 |
| airflow_logs | Airflow 日志 |
| clickhouse_data | ClickHouse 分析数据 |
| langfuse_v3_postgres_data | Langfuse PostgreSQL 数据 |
| langfuse_v3_minio_data | Langfuse MinIO 存储 |

### 参考文档
[opensearch](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/docker/#docker-environment-variables)