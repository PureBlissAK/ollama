"""API route handlers for Ollama."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["inference"])


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/models")
async def list_models():
    """List available models."""
    return {
        "models": [
            {"name": "llama2", "size": "7b"},
            {"name": "mistral", "size": "7b"},
        ]
    }


@router.post("/generate")
async def generate(request: dict):
    """Generate text endpoint."""
    return {
        "model": request.get("model"),
        "response": "Generated response",
        "done": True,
    }
