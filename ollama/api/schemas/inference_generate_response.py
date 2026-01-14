"""Schemas: Inference GenerateResponse."""

from pydantic import BaseModel


class GenerateResponse(BaseModel):
    """Response from text generation."""

    model: str
    prompt: str
    response: str
    done: bool
    total_duration: int
    prompt_eval_count: int
    eval_count: int
