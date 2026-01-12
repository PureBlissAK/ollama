"""Text generation API routes"""
from typing import Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ollama.services.ollama_client import get_ollama_client, GenerateRequest as OllamaGenerateRequest

router = APIRouter()


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
        client = get_ollama_client()
        
        # Convert to Ollama client request
        ollama_request = OllamaGenerateRequest(
            model=request.model,
            prompt=request.prompt,
            stream=False,
            temperature=request.options.get("temperature") if request.options else None,
            top_p=request.options.get("top_p") if request.options else None,
            top_k=request.options.get("top_k") if request.options else None
        )
        
        # Call Ollama
        data = await client.generate(ollama_request)
        
        return GenerateResponse(
            model=data.get("model", request.model),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat() + "Z"),
            response=data.get("response", ""),
            done=data.get("done", True)
        )
        
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
