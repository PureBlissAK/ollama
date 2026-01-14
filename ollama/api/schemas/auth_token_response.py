"""Schema: TokenResponse for authentication endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
