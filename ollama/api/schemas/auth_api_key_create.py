"""Schema: APIKeyCreate for authentication endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating an API key"""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Descriptive name for the API key"
    )
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Key expiration in days")
