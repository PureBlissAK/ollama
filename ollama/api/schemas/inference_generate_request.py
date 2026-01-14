"""Schemas: Inference GenerateRequest."""

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request for text generation."""

    model: str = Field(..., description="Model name (e.g., 'llama2:latest')")
    prompt: str = Field(..., description="Input prompt for generation")
    system: str | None = Field(None, description="System prompt for context")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling")
    top_k: int = Field(40, ge=1, description="Top-K sampling")
    repeat_penalty: float = Field(1.1, ge=0.0, description="Repetition penalty")
    num_predict: int = Field(100, ge=1, le=4096, description="Max tokens to generate")
    stream: bool = Field(True, description="Stream response tokens")
