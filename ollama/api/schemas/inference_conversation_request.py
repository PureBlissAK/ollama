"""Schemas: Inference ConversationRequest."""

from pydantic import BaseModel, Field

from ollama.api.schemas.inference_conversation_message import ConversationMessage


class ConversationRequest(BaseModel):
    """Request for conversation with context."""

    model: str = Field(..., description="Model for generation")
    messages: list[ConversationMessage] = Field(..., description="Conversation history")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    stream: bool = Field(True, description="Stream response")
