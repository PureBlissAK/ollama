"""Authentication API Schemas re-exports.

This module maintains backward compatibility by re-exporting auth-related
schemas from their single-class modules.
"""

from ollama.api.schemas.auth_api_key_create import APIKeyCreate
from ollama.api.schemas.auth_api_key_list import APIKeyList
from ollama.api.schemas.auth_api_key_response import APIKeyResponse
from ollama.api.schemas.auth_login_request import LoginRequest
from ollama.api.schemas.auth_password_change import PasswordChange
from ollama.api.schemas.auth_refresh_token_request import RefreshTokenRequest
from ollama.api.schemas.auth_token_response import TokenResponse
from ollama.api.schemas.auth_user_create import UserCreate
from ollama.api.schemas.auth_user_response import UserResponse

__all__ = [
    "UserCreate",
    "UserResponse",
    "TokenResponse",
    "LoginRequest",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyList",
    "PasswordChange",
    "RefreshTokenRequest",
]
