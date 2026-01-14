"""Schema: UserResponse for authentication endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Schema for user response"""

    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
