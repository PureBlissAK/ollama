"""Schema: APIKeyResponse for authentication endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyResponse(BaseModel):
    """Schema for API key response"""

    id: UUID
    name: str
    key: Optional[str] = Field(None, description="Plain text key (only returned on creation)")
    key_prefix: str = Field(..., description="First 8 characters of key for identification")
    user_id: UUID
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
