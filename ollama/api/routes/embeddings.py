"""Embeddings endpoints"""
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class EmbeddingsRequest(BaseModel):
    """Embeddings request model"""
    model: str = Field(..., description="Model name for embeddings")
    prompt: str = Field(..., description="Text to embed")


class EmbeddingsResponse(BaseModel):
    """Embeddings response model"""
    embedding: List[float] = Field(..., description="Vector embedding")


@router.post("/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(request: EmbeddingsRequest):
    """
    Generate text embeddings
    
    Returns vector representation of input text for semantic search
    """
    # TODO: Implement actual embeddings generation
    # Return placeholder 384-dim vector (all-minilm-l6-v2 size)
    return EmbeddingsResponse(
        embedding=[0.0] * 384
    )
