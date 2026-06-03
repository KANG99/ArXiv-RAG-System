# ArXiv-RAG-System

创建在ArXiv文档数据基础上，生产级别RAG应用，方便迁移到其他数据项目。本项目是对其他开源项目的二次开发，[原始参考项目地址](https://github.com/jamwithai/production-agentic-rag-course)。

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/telegram_and_agentic_ai.png width=330 height=300 title=“图片来源：production-agentic-rag-course”>

## 本次项目主要完成的工作：

- 完成代码梳理，明确项目核心业务流程及技术实现，整理创建梳理文档，方便扩展及项目维护。
- 部署升级程序运行环境，将opensearch及airflow从2.x升级到3.x,提升系统安全性和稳定性。
- ollama升级为0.24.0，使用qwen3.5:4b模型替代llama3.2:1b，提升模型在中文环境的支持。
- 优化PDF文档内容提取，从docling元素提取段落修改为docling生成的节点提取段落，避免解析错误及无效字符。
- 实现QwenEmbeddingsClient类,实现本地qwen3-embedding:0.6b模型为论文片段做embedding向量。
- 抽象出embedding客户端的父类EmbeddingsClient实现本地和Jina服务端embedding统一接口调用。
- 根据国内办公软件使用情况，将推送消息服务从telegram迁移到企业微信及钉钉，提升实际使用便利性。
- **fix**:添加docling模型数据持久化，避免重复从hf下载模型。添加pdf数据持久化及卷映射，方便查看原始文档。
- **fix**:dockerfile添加部分安装依赖，比如`libgl1`,`libglib2.0-0`,`tzdata`等，设置时区，消除对OpenGL的依赖问题等。
- **fix**:修复原始parser.py模块误用await导致程序报错的bug。
- **fix**:删除原是项目中src文件夹下没有被调用的创建数据库单例的database.py模块。
- **fix**:dags/arxiv_ingestion/indexing.py模块使用使@lru_cache 复用数据库连接池，避免重复创建和销毁的开销。
- **fix**:修复text_chunker.py模块中114行调用_reconstruct_text传入参数错误的bug.

## 内容概览

### [完整生产级技术栈](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/production%20tech%20stack.md)
  - FastAPI 
  - PostgreSQL 17
  - OpenSearch 3.6.0
  - Apache Airflow 3.2.1
  - Ollama 0.24.0

### [Docker Compose服务架构](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/docker%20compose.md)
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

### Airflow Dag任务

#### 数据管道相关

- 数据管道完成数据获取、入库、文本切片、embeddingg、创建opensearch搜索索引，具体代码梳理请查看[详细代码介绍](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/data%20pipeline.md)以及[源文件结构及层级依赖关系](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/source_dt.md)。
- [fetch_daily_papers](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/dags/arxiv_ingestion/fetching.py)：arxiv论文数据抓取、下载、docling文本解析解析、postgresql数据入库。

  ```
  fetch_daily_papers (上游任务)
      │  results = {
      │      "papers_fetched": 15,
      │      "papers_stored": 12,
      │      "date": "20260531",
      │      ...
      │  }
      │  ti.xcom_push(key="fetch_results",value=results)
      │      ↓
      │  [XCom 存储]
      │      ↓
      │  ti.xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")
  index_papers_hybrid (下游任务)
  ```

- [index_papers_hybrid](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/dags/arxiv_ingestion/indexing.py)：获取近期存储在postgres的论文内容，按论文章节拆分文本片段，利用Jina或者qwen做embedding。把拆分好的文本片段和它对应的向量数据，一起上传到 OpenSearch，让系统做好分类、归档，后续能快速检索匹配内容。
  - 通过混合检索的方式，获取与问题相关内容。
    ```
    查询输入
      │
      ├──► BM25 搜索 ──► chunk_text, title, abstract
      │                   (关键词匹配)
      │
      ├──► 向量搜索 ──► embedding (1024维)
      │                   (余弦相似度)
      │
      └──► RRF 融合 ◄── 合并两个搜索结果(Reciprocal Rank Fusion)
    ```
  - 通过opensearch dashboard可以在网页上查看简历的索引内容，选择相应的字段，输入查询查看RRF评分，可以排查输出结果是在索引简历上还是模型输出上出现问题。
    
    <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/opensearch%20dashboard.png width=600 height=400 title="opensearch dashboard展示">

## 快速开始
```bash
cd ArXiv-RAG-System
docker compose up -d --remove-orphans
```

