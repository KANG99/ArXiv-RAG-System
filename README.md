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

##### 数据管道相关（由函数[fetch_daily_papers](https://github.com/KANG99/ArXiv-RAG-System/blob/main/airflow/dags/arxiv_ingestion/fetching.py)最终实现）

- arxiv包：
  - client.py模块：定义arxiv论文爬虫客户端`ArxivClient`类，该类定义了爬取论文查询页面、解析查询页面、下载论文方法。爬取网页过程中添加了频率限制及错误重试机制。通过解析网页方法，提取查询到的论文标题、url等网页内容，返回`ArxivPaper`对象列表或者单个对象。下载论文的方法通过提取到的论文url将论文保存成PDF格式文档。
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
- pdf_parser包：
  - docling.py模块：创建了`DoclingParser`类，其中`parse_pdf` 方法完成pdf文档解析完整过程，最终返回由章节列表、纯文本内容、PDF解析器标识、元数据构成的PdfContent（考虑到处理时间和内存消耗没有提取图表）。在对PDF进行解析之前会进行多重验证：
    - 文件是否存在且非空
    - 文件大小是否超过限制
    - 文件是否正确的PDF文件（检测文件头是否为PDF）
    - 文件页数是否超过限制
    ```python
    # src/schemas/pdf_parser/models.py
    class PdfContent(BaseModel):
      """PDF-specific content extracted by parsers like Docling."""
  
      sections: List[PaperSection] = Field(default_factory=list, description="Paper sections")
      figures: List[PaperFigure] = Field(default_factory=list, description="Figures")
      tables: List[PaperTable] = Field(default_factory=list, description="Tables")
      raw_text: str = Field(..., description="Full extracted text")
      references: List[str] = Field(default_factory=list, description="References")
      parser_used: ParserType = Field(..., description="Parser used for extraction")
      metadata: Dict[str, Any] = Field(default_factory=dict, description="Parser metadata")
    ```
  
  - parser.py模块:定义了`PDFParserService`类,用来示例话‘DoclingParser’对象及调用`parse_pdf`方法。
  - factory.py模块:定义`make_pdf_parser_service`函数创建PDFParserService实例。
- metadata_fetcher.py模块：通过定义`class MetadataFetcher`类，实现数据爬取、批量下载、文档解析、元数据序列化入库完整流程方法，通过`def make_metadata_fetcher`函数，配置返回 `MetadataFetcher`实例。

### 本次项目主要完成的工作：

- 完成代码梳理，部署升级程序运行环境，将opensearch及airflow从2.x升级到3.x,提升系统安全性和稳定性 。
- ollama升级为0.24.0，使用qwen3.5:4b模型替代llama3.2:1b，提升模型在中文环境的支持。
- 根据国内办公软件使用情况，将推送消息服务从telegram迁移到企业微信及钉钉，提升实际使用便利性。
- 增强数据管道鲁棒性，解决访问限制429的问题。

## 快速开始
```bash
cd ArXiv-RAG-System
docker compose up -d --remove-orphans
```

