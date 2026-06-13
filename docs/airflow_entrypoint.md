# Airflow 3.x vs 2.x 核心组件差异

本文档整理了 Airflow 3.x 与 2.x 在核心组件上的架构差异。

---

## 核心组件对比表

| 组件 | 2.x 版本 | 3.x 版本 | 
|------|----------|----------|
| **dag-processor** | 默认内嵌在 scheduler 进程内部作为子进程运行，可通过配置独立出来 | **强制独立组件**，调度器不再负责任何 DAG 文件解析 |
| **scheduler** | "巨无霸"进程：读写数据库 + 解析 DAG 文件 + 计算调度 | 职责变轻：只负责检查元数据库并决定**什么时候**执行什么任务 |
| **triggerer** | 仅在使用 Deferrable Operators（延迟算子）时需要启动 | 异步触发器的使用场景被进一步规范 |
| **api-server** | 不存在此组件，由 Webserver 同时负责渲染前端 UI 和提供 REST API | **全新核心组件**，基于 FastAPI 构建，取代 Webserver 核心<br><br>所有 Worker 节点、任务、前端 UI 都**不再直接连接数据库**，必须调用此 api-server |

---

## 架构变更总结

### 职责分离
- **DAG 解析**：从 scheduler 剥离，由独立的 dag-processor 负责
- **调度决策**：scheduler 专注于调度逻辑
- **API 服务**：统一通过 api-server 访问，实现数据库访问层的统一管理

### 核心优势
1. **资源优化**：scheduler 资源消耗显著降低
2. **职责清晰**：各组件职责单一，便于维护和扩展
3. **安全性提升**：Worker 和前端不再直接连接数据库，减少攻击面
4. **可扩展性**：api-server 作为统一入口，便于水平扩展

---

## 参考文献

[1] Apache Airflow 3.0 Documentation  
[2] Airflow 3.0 Architecture Changes  
[3] Airflow 3.0 Migration Guide
