"""Schema: LoginRequest for authentication endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for login request"""

    username: str
    password: str
