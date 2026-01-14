"""Schema: PasswordChange for authentication endpoints."""

from pydantic import BaseModel, Field


class PasswordChange(BaseModel):
    """Schema for password change"""

    old_password: str
    new_password: str = Field(..., min_length=8)
