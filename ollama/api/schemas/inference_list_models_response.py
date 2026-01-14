"""Schemas: ListModelsResponse for inference models endpoint."""

from pydantic import BaseModel

from ollama.services.models import Model


class ListModelsResponse(BaseModel):
    """Response containing available models."""

    models: list[Model]
    total: int
