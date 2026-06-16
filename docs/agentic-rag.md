# src/services/agents

Agentic RAG 工作流模块，基于 LangGraph 实现智能化的检索增强生成流程。

## 目录结构

```
agents/
├── agentic_rag.py    # 核心服务类，基于 LangGraph 构建工作流
├── context.py        # Context：运行时依赖注入上下文
├── config.py         # GraphConfig：工作流配置模型
├── state.py          # AgentState：TypedDict 工作流状态定义
├── prompts.py        # 各种提示词模板
├── models.py         # Pydantic 数据模型（GuardrailScoring、RoutingDecision 等）
├── tools.py          # create_retriever_tool：LangChain 检索工具
├── factory.py        # make_agentic_rag_service：工厂函数
└── nodes/            # 工作流节点实现
    ├── guardrail_node.py        # guardrail 验证节点
    ├── out_of_scope_node.py     # 非学术问题处理节点
    ├── retrieve_node.py         # 文档检索节点
    ├── grade_documents_node.py  # 文档相关性评估节点
    ├── rewrite_query_node.py    # 查询改写节点
    └── generate_answer_node.py  # 答案生成节点
```

## 核心组件

- agentic_rag.py - AgenticRAGService：基于 LangGraph StateGraph 的核心服务类，定义工作流图结构、节点路由和执行逻辑，支持 Langfuse 分布式追踪
- context.py - Context：dataclass 格式的运行时依赖注入类，包含 ollama_client、opensearch_client、embeddings_client、langfuse_tracer 等服务客户端及配置参数
- config.py - GraphConfig：Pydantic 配置模型，控制 max_retrieval_attempts、guardrail_threshold、model、temperature、top_k、use_hybrid 等工作流参数
- state.py - AgentState：TypedDict 工作流状态，定义 messages、original_query、rewritten_query、guardrail_result、routing_decision、sources 等状态字段
- prompts.py：包含 guardrail_prompt、rewrite_prompt、grade_documents_prompt、generate_answer_prompt 等提示词模板
- models.py：Pydantic 模型定义，包括 GuardrailScoring（二分类评分）、GradeDocuments（二值相关性）、SourceItem（来源信息）、ToolArtefact（工具结果）、RoutingDecision（路由决策）、GradingResult（评估结果）
- tools.py - create_retriever_tool：基于 OpenSearch 和 EmbeddingsClient 的 LangChain 检索工具封装
- factory.py - make_agentic_rag_service：工厂函数，通过依赖注入创建 AgenticRAGService 实例

## 工作流节点

- guardrail_node.py - ainvoke_guardrail_step：guardrail 验证节点，用 LLM 评估用户问题是否属于 CS/AI/ML 研究范畴（0-100 分），低于阈值则路由到 out_of_scope
- out_of_scope_node.py - ainvoke_out_of_scope_step：非学术问题处理节点，对闲聊、常识等问题给出友好拒绝回答
- retrieve_node.py - ainvoke_retrieve_step：文档检索节点，调用 create_retriever_tool 从 OpenSearch 获取论文片段
- grade_documents_node.py - ainvoke_grade_documents_step：文档相关性评估节点，用 LLM 判断检索到的文档是否与问题相关（yes/no）
- rewrite_query_node.py - ainvoke_rewrite_query_step：查询改写节点，如果文档不相关则改写问题后重试检索（最多 2 次）
- generate_answer_node.py - ainvoke_generate_answer_step：答案生成节点，基于检索到的论文上下文生成最终答案
