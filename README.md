# ArXiv-RAG-System

## 内容预览

创建在ArXiv文档数据基础上，生产级别RAG应用，方便迁移到其他数据项目。本项目是对其他开源项目的二次开发，[原始参考项目地址](https://github.com/jamwithai/production-agentic-rag-course)。

### [完整生产级技术栈](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/production%20tech%20stack.md)
  - FastAPI 
  - PostgreSQL 17
  - OpenSearch 3.6.0
  - Apache Airflow 3.2.0
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

### [源文件结构及层级依赖关系](https://github.com/KANG99/ArXiv-RAG-System/blob/main/docs/source_dt.md)
#### 根目录
- config.py：基于`BaseConfigSettings`定义各种客户端类参数配置类，比如`ArxivSettings`,`PDFParserSettings`类等。定义get_settings()函数，返回Settings对象，里面定义了各种基础参数及客户端类参数配置对象。

#### services库
##### 数据管道（fetch_daily_papers）
- arxiv包：
  - client.py模块：定义arxiv论文爬虫客户端`ArxivClient`类，该类定义了爬取网页查询页面、解析查询网页、下载论文方法。爬取网页过程中添加了频率限制及错误重试机制。通过解析网页方法，提取网页内容，返回`ArxivPaper`对象列表或者单个对象。下载论文的方法通过提取到的论文url将论文保存成PDF格式文档。
    ```python
    # src/schemas/arxiv/paper.py
    class ArxivPaper(BaseModel):
        """Schema for arXiv API response data."""
    
        arxiv_id: str = Field(..., description="arXiv paper ID")
        title: str = Field(..., description="Paper title")
        authors: List[str] = Field(..., description="List of author names")
        abstract: str = Field(..., description="Paper abstract")
        categories: List[str] = Field(..., description="Paper categories")
        published_date: str = Field(..., description="Date published on arXiv (ISO format)")
        pdf_url: str = Field(..., description="URL to PDF")
    ```
  - factory.py模块:定义`make_arxiv_client`函数用来创建ArxivClient实例。
- 
### 本次项目主要完成的工作：
- 部署升级程序运行环境，将opensearch及airflow从2.x升级到3.x,提升系统安全性和稳定性 。
- ollama升级为0.24.0，使用qwen3.5:4b模型替代llama3.2:1b，提升模型在中文环境的支持。
- 根据国内办公软件使用情况，将推送消息服务从telegram迁移到企业微信及钉钉，提升实际使用便利性。

## 快速开始


```bash
cd ArXiv-RAG-System
docker compose up -d --remove-orphans
```

