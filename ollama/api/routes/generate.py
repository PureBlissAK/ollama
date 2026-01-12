"""Text generation endpoints"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

router = APIRouter()

OLLAMA_API_URL = "http://localhost:8000/api"


class GenerateRequest(BaseModel):
    """Generate request model"""
    model: str = Field(..., description="Model name to use for generation")
    prompt: str = Field(..., description="Prompt text")
    stream: bool = Field(default=False, description="Stream response")
    options: Optional[dict] = Field(default=None, description="Generation options")


class GenerateResponse(BaseModel):
    """Generate response model"""
    model: str
    created_at: str
    response: str
    done: bool


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate text completion from a prompt
    
    Performs inference using the specified model and returns generated text
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_API_URL}/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": request.options or {}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return GenerateResponse(
                model=data.get("model", request.model),
                created_at=data.get("created_at", datetime.now(timezone.utc).isoformat() + "Z"),
                response=data.get("response", ""),
                done=data.get("done", True)
            )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )
