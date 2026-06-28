# ArXiv-RAG-System

本项目是基于[jamwithai/production-agentic-rag-course](https://github.com/jamwithai/production-agentic-rag-course)的二次开发。创建在ArXiv文档数据基础上，在Docker容器部署的生产级别RAG应用，实现系统中文本土化，方便迁移到其他数据项目。

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/telegram_and_agentic_ai.png  title=“图片来源：production-agentic-rag-course”>

## 本次项目主要完成的工作：

- 完成代码梳理，明确项目核心业务流程及技术实现，整理创建梳理文档，方便扩展及项目维护。
- 部署升级程序运行环境，将opensearch及airflow从2.x升级到3.x,提升系统安全性和稳定性。
  - 将airflow从2.10.3升级到3.2.1,实现全架构解耦，[启动脚本](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/entrypoint.sh)必须作出如下调整：1.airflow dag-processor（独立进程强制化）；2.airflow scheduler（职责变轻）；3.airflow triggerer（异步触发器）；4.airflow api-server（全新核心组件，取代 Webserver 核心功能）[具体查看](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/airflow_entrypoint.md)。进行了上述核心调整后，添加了看门狗机制，监控核心组件健康状况。
  - 将opensearch从2.19.0升级到3.6.0,提升系统安全性和稳定性。2.修改compose.yml文件，将plugins.security.disabled=true设置为false,使用官方测试专用证书（Demo Certs）测试,更贴近生产环境。
- 将langfuse从3.x升级到4.x，直接废弃servicese\langfuse包，使用v4上下文管理模式，简化代码结构。
- 为了最优化M系列芯片性能，将ollama部署从docker替换到本地，升级ollama模型为qwen3.6:35b-mlx,提升模型性能及响应速度及模型对中文的准确性。
- 优化PDF文档内容提取，从docling元素提取段落修改为docling生成的节点提取段落，避免解析错误及无效字符。
- 实现QwenEmbeddingsClient类,实现本地qwen3-embedding:4b模型为论文片段做1024维embedding向量。
- 抽象出embedding客户端的父类EmbeddingsClient实现本地和Jina服务端embedding统一接口调用。
- 添加问题翻译模块，使用将用户输入的问题翻译为英文，提升问题检索能力。
- 完成搜索系统性能评估，执行响应时间、吞吐量、recall@10、precision@10等指标性能测试。
  ```
  ================================================================================
  搜索类型      平均响应时间    吞吐量         Recall@10  Precision@10  
  --------------------------------------------------------------------------------
  BM25          52ms        ~200 req/s       0.78        0.65          
  向量          105ms        ~95 req/s        0.82        0.71          
  混合(RRF)     2400ms       ~25 req/s        0.89        0.84          
  ================================================================================
  ```
- 根据国内社交软件的使用情况，将消息收发服务从telegram迁移到QQ机器人，提升实际使用便利性。（目前只支持文本模式，持续完善图片和语音模式）
- [部分代码修复及配置调整](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/fix.md)

## 内容概览

### [完整生产级技术栈](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/production%20tech%20stack.md)
  - FastAPI 0.136.1
  - PostgreSQL 17
  - OpenSearch 3.6.0
  - Apache Airflow 3.2.1
  - Ollama 0.24.0
  - redis 7

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

### Airflow 数据管道相关任务

<img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/airflow%20dags.png title="airflow data pipeline">

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

- [index_papers_hybrid](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/dags/arxiv_ingestion/indexing.py)：获取上文存储在postgres的论文内容，如果上游任务不存则获取前一天的论文内容。按论文章节拆分文本片段，利用Jina或者qwen做embedding。把拆分好的文本片段和它对应的向量数据以及论文标题、id等，建立OpenSearch索引，让系统做好分类、归档，后续能快速检索匹配内容。
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
  - 通过opensearch dashboard可以在网页上查看简历的索引内容，选择相应的字段，输入查询查看RRF评分，可以排查输出结果是在索引建立上还是模型输出上出现问题。
    
    <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/opensearch%20dashboard.png title="opensearch dashboard展示">

- [generate_daily_report](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/dags/arxiv_ingestion/reporting.py):产生追踪每日论文抓取和索引进度,监控 OpenSearch 索引大小，记录每日执行情况的日志报告。快速用于定位失败环节，监控和分析数据管道的运行状态。

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/daily_report.png title="opensearch dashboard展示">

### LLM服务

- 使用ollama部署LLM服务，由[自定义ollama库](https://github.com/KANG99/ArXiv-RAG-System/tree/main/src/services/ollama)提供相应的服务支持。使用了redis缓存问答的方式，提升响应效率。[具体代码介绍](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/ollama%20serve.md)。
- 由于是在M系列芯片上开发该项目，为了发挥M芯片的最佳性能，提升LLM生成token的速度。将ollama服务部署在了本地。

### FastAPI服务

- 使用FastAPI实现web后端服务，如图所示定义了健康检查端点、基础RAG LLM问答端点、混合搜索端点、Agentic RAG问答端点。具体查看[API服务具体代码梳理](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/web%20services.md)。

- Agentic RAG问答端点：由基于 LangGraph 构建的 [Agentic RAG服务包](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/agentic-rag.md)支撑。接收用户的学术问题，非学术问题以友好方式拒绝回答，通过多层智能节点协作，从 arXiv论文数据库中检索相关信息并生成回答。

  - 工作流：

    ```
    START → guardrail（安全校验）
              ├─ score ≥ threshold → retrieve（检索论文）→ tool_retrieve（工具执行）
              │                                                ↓
              │                                         grade_documents（文档评分）
              │                                            ↓
              │                          ┌───────────────┴───────────────┐
              │                          is_relevant=yes                    is_relevant=no
              │                                  ↓                         ↓
              │                         generate_answer（生成答案）      rewrite_query（改写问题）
              │                                                        ↓
              │                                                   retrieve（重试检索）...
              │                                                          ↓
              └─ score < threshold → out_of_scope（超出范围）→ END
    ```
  - 各个节点职责

    | Node | 作用 |
    |------|------|
    | guardrail | 用 LLM 评估用户问题是否属于 CS/AI/ML 研究范畴，给出 0-100 评分 |
    | out_of_scope | 对非学术问题（如闲聊、常识）给出友好拒绝回答 |
    | retrieve | 触发论文检索工具调用 |
    | tool_retrieve | 实际执行检索，从 OpenSearch 获取论文片段 |
    | grade_documents | LLM 评判检索到的文档是否相关（yes/no） |
    | rewrite_query | 如果文档不相关，改写问题后重试检索（最多 2 次） |
    | generate_answer | 基于检索到的论文上下文生成最终答案 |


- 启动langfuse服务，实现对 RAG 流程各阶段的追踪和监控。

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/langfuse-web.jpeg title="langfuse website">

- 使用gradio构建问答前段问答页面

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/gradio.png title="gradio QA website">

### QQ机器人

- QQ接入RAG系统，实现用户使用QQ机器人进行问答，如图所示。

  <img src=https://github.com/KANG99/ArXiv-RAG-System/blob/main/images/QQBot.jpeg title="QQBot">

  ps：目前只支持文本模式，持续完善图片和语音模式。


## 快速开始

- 配置环境变量
  - 复制.env_example文件到.env文件
  - 根据实际情况修改.env文件中的环境变量
  ```bash
  cp .env_example .env
  nano .env
  ```
  - 主要修改内容：
    - 修改JINA_API_KEY为自己的Jina API密钥（只是用本地向量转换不配置）
    - 修改QQ__APP_ID为自己的QQ机器人ID
    - 修改QQ__APP_SECRET为自己的QQ机器人Secret
    - 修改LANGFUSE__PUBLIC_KEY为自己的langfuse公钥
    - 修改LANGFUSE__SECRET_KEY为自己的langfuse密钥

- 打开docker镜像环境
  ```bash
  cd ArXiv-RAG-System
  docker compose up -d --remove-orphans
  ```

- 打开本地ollama服务，手动安装模型（也可以取消compose.yml对ollama镜像的注释，直接在docker运行）
  ```
  # 打开ollama服务
  ollama serve
  #安装qwen3-embedding:4b
  ollama pull qwen3-embedding:4b
  #安装qwen3.6:35b-mlx 
  ollama pull qwen3.6:35b-mlx
  ```

- 端口测试（ask端口为例）
  ```
  curl -X POST "http://localhost:8000/api/v1/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "请为我介绍一下基于koopman算子理论的adakoop算法", "top_k": 3}' \
    | jq .
  ```

- 打开gradio网页页面,进行页面问答
  ```bash
  cd src
  uv run python gradio_app.py
  ```
