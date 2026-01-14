"""Schemas: ChatRequest for /chat route."""

from pydantic import BaseModel, Field

from ollama.api.schemas.chat_message import Message


class ChatRequest(BaseModel):
    """Chat request model"""

    model: str = Field(..., description="Model name")
    messages: list[Message] = Field(..., description="Chat messages")
    stream: bool = Field(default=False, description="Stream response")
    options: dict | None = Field(default=None, description="Generation options")
