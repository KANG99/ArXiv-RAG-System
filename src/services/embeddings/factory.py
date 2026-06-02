from typing import Optional

from src.config import Settings, get_settings

from .qwen_client import QwenEmbeddingsClient


def make_embeddings_service(settings: Optional[Settings] = None) -> QwenEmbeddingsClient:
    """Factory function to create embeddings service.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: QwenEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key

    return QwenEmbeddingsClient(api_key=api_key)


def make_embeddings_client(settings: Optional[Settings] = None) -> QwenEmbeddingsClient:
    """Factory function to create embeddings client.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: QwenEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key

    return QwenEmbeddingsClient(api_key=api_key)
