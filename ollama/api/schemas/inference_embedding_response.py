"""Schemas: Inference EmbeddingResponse."""

from pydantic import BaseModel


class EmbeddingResponse(BaseModel):
    """Response with embeddings."""

    embedding: list[float]
    model: str
    dimensions: int
