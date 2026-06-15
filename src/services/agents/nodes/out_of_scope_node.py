import logging
from typing import Dict, List

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from ..context import Context
from ..state import AgentState
from .utils import get_latest_query

logger = logging.getLogger(__name__)


async def ainvoke_out_of_scope_step(
    state: AgentState,
    runtime: Runtime[Context],
) -> Dict[str, List[AIMessage]]:
    """Handle out-of-scope queries with a helpful message.

    This node responds to queries that are outside the domain of
    CS/AI/ML research papers with a polite, informative message.

    :param state: Current agent state
    :param runtime: Runtime context (not used in this node)
    :returns: Dictionary with messages containing the out-of-scope response
    """
    logger.info("NODE: out_of_scope")

    question = get_latest_query(state["messages"])

    # Generate helpful response message
    response_text = (
"很抱歉，我只能帮助解答关于计算机科学、人工智能和机器学习领域来自 arXiv 的学术研究论文问题。\n\n"
f"您的问题：'{question}'\n\n"
"这似乎超出了我的专业范围。对于此类问题，您可以尝试：\n"
"- 通用的 AI 助手来获取广泛的知识\n"
"- CS/AI/ML 之外主题的领域特定资源\n"
"- 特定软件/工具的技术文档\n\n"
"如果您有关于 AI/ML 研究论文的问题，我很乐意帮助！"
    )

    logger.info("Responding with out-of-scope message")

    return {"messages": [AIMessage(content=response_text)]}
