import logging
from typing import Optional

import botpy
import httpx

from src.config import get_settings
from src.services.qq.bot import QQBot

logger = logging.getLogger(__name__)


def make_qq_service()->Optional[QQBot]:
    """
    Create QQ bot if enabled.
    
    Args:
        opensearch_client: OpenSearch client
        embeddings_client: Embeddings service client
        ollama_client: Ollama LLM client
        cache_client: Optional cache client
        langfuse_tracer: Optional Langfuse tracer (not used)
        
    Returns:
        QQBot instance or None if disabled
    """
    settings = get_settings()
    
    if not settings.qq.enabled:
        logger.info("QQ bot is disabled")
        return None

    if not settings.qq.app_id:
        logger.warning("QQ bot app_id not configured")
        return None
    
    if not settings.qq.app_secret:
        logger.warning("QQ bot app_secret not configured")
        return None
    
    logger.info("Initializing QQ bot...")
    bot = QQBot(
        intents=botpy.Intents(public_messages=True),
    )
    
    logger.info("QQ bot created successfully")
    return bot
