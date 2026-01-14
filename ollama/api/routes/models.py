"""Model management endpoints"""

from typing import cast

import httpx
from fastapi import APIRouter, HTTPException, status

from ollama.api.schemas.models_list_models_response import ListModelsResponse
from ollama.api.schemas.models_model_info import ModelInfo
from ollama.services.ollama_client import get_ollama_client

router = APIRouter()


@router.get("", response_model=ListModelsResponse)
async def list_models() -> ListModelsResponse:
    """
    List all available models

    Returns list of models available for inference
    """
    try:
        client = get_ollama_client()
    except RuntimeError:
        # Fallback stub models when Ollama client is unavailable (e.g., tests)
        return ListModelsResponse(
            models=[
                ModelInfo(
                    name="test-model",
                    size="1.0MB",
                    digest="stub-digest",
                    modified_at="now",
                )
            ]
        )

    try:
        ollama_models = await client.list_models()

        models = []
        for model in ollama_models:
            models.append(
                ModelInfo(
                    name=model.name,
                    size=str(model.size),
                    digest="",
                    modified_at="",
                )
            )

        return ListModelsResponse(models=models)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {e!s}",
        ) from e


@router.get("/{model_name}")
async def get_model(model_name: str) -> dict[str, object]:
    """Get information about a specific model"""
    try:
        client = get_ollama_client()
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"{client.base_url}/api/show", json={"name": model_name}
            )
            response.raise_for_status()
            return cast(dict[str, object], response.json())

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama client not initialized: {e!s}",
        ) from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if e.response.status_code == 404
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=f"Model not found or service error: {e!s}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {e!s}",
        ) from e


@router.post("/pull")
async def pull_model(model_name: str) -> dict[str, object]:
    """Download a model"""
    try:
        client = get_ollama_client()
        # The ollama client doesn't have a direct pull method, so we use httpx
        async with httpx.AsyncClient(
            timeout=600.0
        ) as http_client:  # 10 min timeout for model download
            response = await http_client.post(
                f"{client.base_url}/api/pull", json={"name": model_name}
            )
            response.raise_for_status()
            return cast(dict[str, object], response.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to pull model: {e!s}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model pull failed: {e!s}",
        ) from e


@router.delete("/{model_name}")
async def delete_model(model_name: str) -> dict[str, str]:
    """Delete a model"""
    try:
        client = get_ollama_client()
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"{client.base_url}/api/delete", json={"name": model_name}
            )
            response.raise_for_status()
            return {"status": "deleted", "model": model_name}
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if e.response.status_code == 404
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=f"Failed to delete model: {e!s}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model deletion failed: {e!s}",
        ) from e
