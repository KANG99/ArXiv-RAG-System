# src根目录

- dependencies.py：模块定义了 FastAPI 依赖注入（Dependency Injection） ，用于在整个应用中提供可复用的服务实例。服务在应用启动时创建，请求结束时销毁，避免重复创建对象，提高性能。
- radio_app.py模块构建了一个 Gradio 网页界面应用 ，为 ArXiv-RAG-System 提供可视化的交互式问答界面。

