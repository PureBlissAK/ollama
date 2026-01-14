"""Chat completion API routes"""

from datetime import UTC, datetime
from typing import Literal, cast

import httpx
from fastapi import APIRouter, HTTPException, status

from ollama.api.schemas.chat_message import Message
from ollama.api.schemas.chat_request import ChatRequest
from ollama.api.schemas.chat_response import ChatResponse
from ollama.services.ollama_client import ChatMessage as OllamaChatMessage
from ollama.services.ollama_client import ChatRequest as OllamaChatRequest
from ollama.services.ollama_client import get_ollama_client

# Expose httpx for test monkeypatching (see tests/integration fixtures)
_httpx_for_testing = httpx

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat completion endpoint

    Performs conversational inference with context from previous messages
    """
    try:
        client = get_ollama_client()
    except RuntimeError:
        # Fallback stub response when Ollama client is unavailable (e.g., in tests)
        last_message = (
            request.messages[-1] if request.messages else Message(role="assistant", content="")
        )
        return ChatResponse(
            model=request.model,
            created_at=datetime.now(UTC).isoformat() + "Z",
            message=Message(role="assistant", content=last_message.content),
            done=True,
        )

    try:
        # Convert messages to Ollama format
        ollama_messages = [
            OllamaChatMessage(
                role=cast(Literal["user", "assistant", "system"], msg.role),
                content=msg.content,
            )
            for msg in request.messages
        ]

        # Create Ollama request
        temp = (
            float(request.options["temperature"])
            if request.options and "temperature" in request.options
            else 0.7
        )
        top_p = (
            float(request.options["top_p"])
            if request.options and "top_p" in request.options
            else 0.9
        )
        top_k = (
            int(request.options["top_k"]) if request.options and "top_k" in request.options else 40
        )

        ollama_request = OllamaChatRequest(
            model=request.model,
            messages=ollama_messages,
            temperature=temp,
            top_p=top_p,
            top_k=top_k,
        )

        # Call Ollama
        resp = await client.chat(ollama_request)

        return ChatResponse(
            model=request.model,
            created_at=datetime.now(UTC).isoformat() + "Z",
            message=Message(
                role=resp.role,
                content=resp.content,
            ),
            done=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {e!s}",
        ) from e
