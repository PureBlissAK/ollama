"""Model management endpoints"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ollama.services.ollama_client import get_ollama_client

router = APIRouter()


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    size: str
    digest: str
    modified_at: str


class ListModelsResponse(BaseModel):
    """Response for list models"""
    models: List[ModelInfo]


@router.get("", response_model=ListModelsResponse)
async def list_models():
    """
    List all available models
    
    Returns list of models available for inference
    """
    try:
        client = get_ollama_client()
        ollama_models = await client.list_models()
        
        models = []
        for model in ollama_models:
            # Convert size from bytes to human-readable format
            size_bytes = model.size or 0
            if size_bytes > 1e9:
                size_str = f"{size_bytes / 1e9:.1f}GB"
            elif size_bytes > 1e6:
                size_str = f"{size_bytes / 1e6:.1f}MB"
            else:
                size_str = f"{size_bytes}B" if size_bytes > 0 else "Unknown"
            
            models.append(ModelInfo(
                name=model.name,
                size=size_str,
                digest=model.digest or "",
                modified_at=model.modified_at or ""
            ))
        
        return ListModelsResponse(models=models)
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama client not initialized: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )


@router.get("/{model_name}")
async def get_model(model_name: str):
    """Get information about a specific model"""
    try:
        client = get_ollama_client()
        model_info = await client.show_model(model_name)
        return model_info
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama client not initialized: {str(e)}"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if e.response.status_code == 404 else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not found or service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/pull")
async def pull_model(model_name: str):
    """Download a model"""
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for model download
            response = await client.post(
                f"{OLLAMA_API_URL}/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to pull model: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model pull failed: {str(e)}"
        )


@router.delete("/{model_name}")
async def delete_model(model_name: str):
    """Delete a model"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{OLLAMA_API_URL}/delete",
                json={"name": model_name}
            )
            response.raise_for_status()
            return {"status": "deleted", "model": model_name}
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if e.response.status_code == 404 else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to delete model: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model deletion failed: {str(e)}"
        )
