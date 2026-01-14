"""Schemas: Inference ConversationMessage."""

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Message in conversation history."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
