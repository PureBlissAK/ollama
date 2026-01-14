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
from ollama.auth.middleware import AuthMiddleware, require_auth, verify_token_optional

__all__ = [
    "init_firebase",
    "get_current_user",
    "require_role",
    "require_root_admin",
    "revoke_user_tokens",
    "get_or_create_user",
    "AuthMiddleware",
    "require_auth",
    "verify_token_optional",
]
