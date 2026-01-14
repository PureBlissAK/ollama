"""Schemas: Inference ModelPullRequest."""

from pydantic import BaseModel, Field


class ModelPullRequest(BaseModel):
    """Request to download a model."""

    model_name: str = Field(..., description="Model identifier (e.g., 'llama2:latest')")
