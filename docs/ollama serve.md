# src

## services包

- ollama库
  - client.py - OllamaClient：封装与本地 Ollama 服务的 HTTP 通信，提供健康检查、模型列表查询、文本生成、流式生成、RAG 答案生成等方法
  - factory.py - make_ollama_client：使用 @lru_cache 单例模式创建全局唯一的 OllamaClient 实例，减少重复连接开销
  - prompts.py - RAGPromptBuilder/ResponseParser：RAGPromptBuilder 从模板文件加载系统提示词，构建含上下文片段的问答提示；ResponseParser 解析 LLM 返回的 JSON 响应，支持结构化输出和降级提取

- cache库
  - client.py - CacheClient：基于 Redis 的精确匹配缓存客户端，通过 SHA256 哈希请求参数生成缓存键，提供 `find_cached_response()` 查询缓存和 `store_response()` 存储响应方法，支持 TTL 过期策略
  - factory.py - make_cache_client/make_redis_client：Redis 客户端工厂函数，make_redis_client 创建带连接池的 Redis 实例并测试连接，make_cache_client 创建 CacheClient 实例
