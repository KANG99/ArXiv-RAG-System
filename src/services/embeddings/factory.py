from typing import Optional

from src.config import Settings, get_settings

from .embed_client import EmbeddingsClient
from .jina_client import JinaEmbeddingsClient
from .qwen_client import QwenEmbeddingsClient


def make_embeddings_service(settings: Optional[Settings] = None) -> EmbeddingsClient:
    """Factory function to create embeddings service.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: QwenEmbeddingsClient or JinaEmbeddings instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key
    
    subclasses = EmbeddingsClient.__subclasses__()
    for cls in subclasses:
        if cls.satisfies_contract(settings.embedding_contract):
            return cls(api_key)
    else:
        raise Exception("Please set embedding model to Qwen or Jina")


def make_embeddings_client(settings: Optional[Settings] = None) -> EmbeddingsClient:
    """Factory function to create embeddings client.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: QwenEmbeddingsClient or JinaEmbeddings instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key

    subclasses = EmbeddingsClient.__subclasses__()
    for cls in subclasses:
        if cls.satisfies_contract(settings.embedding_contract):
            return cls(api_key)
    else:
        raise Exception("Please set embedding model to Qwen or Jina")
