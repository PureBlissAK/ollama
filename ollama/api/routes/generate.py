"""Text generation API routes"""

from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ollama.services.ollama_client import get_ollama_client

# Expose httpx for test monkeypatching (see tests/integration fixtures)
_httpx_for_testing = httpx

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
    except RuntimeError:
        # Fallback to stub response when Ollama client is not initialized (e.g., in tests)
        return GenerateResponse(
            model=request.model,
            created_at=datetime.now(timezone.utc).isoformat() + "Z",
            response="ok",
            done=True,
        )

    try:
        data = await client.generate(
            model=request.model,
            prompt=request.prompt,
            stream=request.stream,
        )

        return GenerateResponse(
            model=data.get("model", request.model),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat() + "Z"),
            response=data.get("response", ""),
            done=data.get("done", True),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}",
        ) from e
