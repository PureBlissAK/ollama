"""Schemas: Inference EmbeddingRequest."""

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Request for text embedding."""

    text: str = Field(..., description="Text to embed")
    model: str = Field("nomic-embed-text", description="Embedding model to use")
