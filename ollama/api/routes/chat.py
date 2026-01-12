"""Chat completion endpoints"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

router = APIRouter()

OLLAMA_API_URL = "http://localhost:8000/api"


class Message(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request model"""
    model: str = Field(..., description="Model name")
    messages: List[Message] = Field(..., description="Chat messages")
    stream: bool = Field(default=False, description="Stream response")
    options: Optional[dict] = Field(default=None, description="Generation options")


class ChatResponse(BaseModel):
    """Chat response model"""
    model: str
    created_at: str
    message: Message
    done: bool


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat completion endpoint
    
    Performs conversational inference with context from previous messages
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_API_URL}/chat",
                json={
                    "model": request.model,
                    "messages": [msg.model_dump() for msg in request.messages],
                    "stream": False,
                    "options": request.options or {}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return ChatResponse(
                model=data.get("model", request.model),
                created_at=data.get("created_at", datetime.now(timezone.utc).isoformat() + "Z"),
                message=Message(
                    role=data.get("message", {}).get("role", "assistant"),
                    content=data.get("message", {}).get("content", "")
                ),
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
            detail=f"Chat completion failed: {str(e)}"
        )
