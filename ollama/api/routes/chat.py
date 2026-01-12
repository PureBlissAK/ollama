"""Chat completion API routes"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ollama.services.ollama_client import get_ollama_client, ChatRequest as OllamaChatRequest, ChatMessage as OllamaChatMessage

router = APIRouter()


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
        client = get_ollama_client()
        
        # Convert messages to Ollama format
        ollama_messages = [OllamaChatMessage(role=msg.role, content=msg.content) for msg in request.messages]
        
        # Create Ollama request
        ollama_request = OllamaChatRequest(
            model=request.model,
            messages=ollama_messages,
            stream=False,
            temperature=request.options.get("temperature") if request.options else None,
            top_p=request.options.get("top_p") if request.options else None,
            top_k=request.options.get("top_k") if request.options else None
        )
        
        # Call Ollama
        data = await client.chat(ollama_request)
        
        return ChatResponse(
            model=data.get("model", request.model),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat() + "Z"),
            message=Message(
                role=data.get("message", {}).get("role", "assistant"),
                content=data.get("message", {}).get("content", "")
            ),
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
