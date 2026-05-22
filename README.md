# ArXiv-RAG-System

创建在ArXiv文档数据基础上，生产级别RAG应用，方便迁移到其他数据项目。
- [完整生产级技术栈]()
- [Docker Compose服务架构]（）
- [原始参考项目](https://github.com/jamwithai/production-agentic-rag-course)

```
┌─────────────────────────────────────────────────────────────┐
│                    ArXiv-RAG-System                         │
├─────────────────────────────────────────────────────────────┤
│  API (8000)  ←→  Redis  ←→  PostgreSQL  ←→  Airflow(8080)   │
│       ↓                                                     │
│  OpenSearch(9200)  ←→  Ollama(11434)                        │
│       ↓                                                     │
│  OpenSearch Dashboards(5601)                                │
├─────────────────────────────────────────────────────────────┤
│                       Langfuse 可观测性                      ｜
│  Langfuse Web(3001) ←→ Worker(3030) ←→ ClickHouse           │
│                      ←→ Postgres ←→ Redis ←→ MinIO          │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始


```bash
cd ArXiv-RAG-System
docker compose up -d --remove-orphans
```

