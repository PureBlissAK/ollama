"""
Authentication API Schemas
Request/Response models for authentication endpoints
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


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


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class APIKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for the API key")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Key expiration in days")


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


class APIKeyList(BaseModel):
    """Schema for list of API keys"""
    keys: list[APIKeyResponse]
    total: int


class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
