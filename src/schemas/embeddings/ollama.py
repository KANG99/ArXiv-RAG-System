from typing import List

from pydantic import BaseModel


class OllamaEmbeddingRequest(BaseModel):
    """Request model for Ollama embeddings API."""

    model: str
    input: str
    dimensions: int = 1024


class OllamaEmbeddingResponse(BaseModel):
    """Response model from Ollama embeddings API."""

    embedding: List[float]
