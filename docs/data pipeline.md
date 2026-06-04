# src根目录

- config.py：基于`BaseConfigSettings`定义各种客户端类参数配置类，比如`ArxivSettings`,`PDFParserSettings`类等。定义`get_settings`函数，返回Settings对象，里面定义了各种基础参数及客户端类参数配置对象。
- models包里面的`paper.py`模块定义了论文数据在 PostgreSQL 中的存储结构的SQLAlchemy 数据库模型。
- repositories包里面的`paper.py`模块定义了`PaperRepository`类，实现了用于数据库数据增加、更新、查询等操作的方法。

##  services库

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
  
  - parser.py模块:定义了`PDFParserService`类,用来示例话 `DoclingParser`对象及调用`parse_pdf`方法。
  - factory.py模块:定义`make_pdf_parser_service`函数创建PDFParserService实例。
- metadata_fetcher.py模块：通过定义`class MetadataFetcher`类，定义了`fetch_and_process_papers`方法实现数据爬取、批量下载、文档解析、元数据序列化入库完整流程方法，通过`def make_metadata_fetcher`函数，配置返回 `MetadataFetcher`实例。

- repositories包：
 - paper.py模块：创建`PaperRepository`类，定义了数据库的创建、更新和条件查找。

- indexing包：
  - text_chunker.py模块：定义Text,提供文本重叠分段处理服务。采用基于单词的分段方式，分段长度与重叠区间可自定义配置。默认配置：单段 600 词，段间重叠 100 词。
  - hybrid_indexer.py模块:创建`HybridIndexingService`定义`index_paper`方法，实现文本分段和embedding，建立opensearch索引，返回创建状态。
  - factory.py模块：定义`make_hybrid_indexing_service`函数，创建`HybridIndexingService`实例。

- opensearch包：
  - client.py模块:定义了`OpenSearchClient`类，是一个统一的 OpenSearch 客户端封装类。负责管理与 OpenSearch 服务器的连接，提供索引管理能力。支持多种索引搜索模式（BM25、向量、混合），处理文档的增删改查操作。实际上在环境初始化过程就已经通过`OpenSearchClient`里面定义的`setup_indices`方法创建了faiss索引和数据查询管道。
  - index_config_hybrid.py模块：定义 `ARXIV_PAPERS_CHUNKS_MAPPING`产级的混合搜索索引配置。同时支持 BM25 关键词搜索和 HNSW 向量搜索，针对英文文本优化的分析器配置，防止字段污染和意外数据类型导致的搜索错误。与 RRF 管道配合使用，实现混合搜索。
  - factory.py模块：定义`make_opensearch_client`函数用来创建OpenSearchClient单一实例，主要用在读取操作，共享客户端提高效率。要使用多实例时候，使用`make_opensearch_client_fresh`函数创建新的实例，索引操作批量写入时候能够独立的资源链接，允许缩影服务链接到不同的opensearch集群，保证隔离型。
  
- embedding包：   
  - jina_client.py模块：定义`JinaEmbeddingsClient`类，实现在线Jina embedding模型调用
  - qwen_client.py模块：定义`QwenEmbeddingsClient`类，实现本地qwen embedding模型调用。
  - embed_client.py模块：定义`JinaEmbeddingsClient`和`QwenEmbeddingsClient`的抽象父类`EmbeddingsClient`,实现统一接口调用。
  - factory.py模块:根据embedding_contract选择创建适当的embedding client对象，实现在线或者本地文本embedding。
