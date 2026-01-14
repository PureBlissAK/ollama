"""Auth package initialization."""

from __future__ import annotations

from ollama.auth.firebase_auth import (
    get_current_user,
    get_or_create_user,
    init_firebase,
    require_role,
    require_root_admin,
    revoke_user_tokens,
)
from ollama.auth.manager import AuthManager
from ollama.auth.middleware import AuthMiddleware, require_auth, verify_token_optional
from ollama.exceptions.authentication import AuthenticationError

__all__ = [
    "AuthManager",
    "AuthMiddleware",
    "AuthenticationError",
    "get_current_user",
    "get_or_create_user",
    "init_firebase",
    "require_auth",
    "require_role",
    "require_root_admin",
    "revoke_user_tokens",
    "verify_token_optional",
]
