"""Authentication and Authorization domain.

Top-level imports are attempted but optional dependencies (e.g., FastAPI)
may be unavailable in lightweight test environments. We import lazily and
fall back to a minimal export set when those dependencies are missing so
unit tests that import submodules (like `zero_trust`) can run without
installing full runtime dependencies.
"""

try:
    from .impl.firebase_auth import (
        get_current_user,
        get_or_create_user,
        init_firebase,
        require_role,
        require_root_admin,
        revoke_user_tokens,
    )
    from .impl.manager import AuthManager
    from .impl.middleware import require_auth, verify_token_optional

    __all__ = [
        "init_firebase",
        "get_current_user",
        "get_or_create_user",
        "require_role",
        "require_root_admin",
        "revoke_user_tokens",
        "require_auth",
        "verify_token_optional",
        "AuthManager",
    ]
except Exception:  # pragma: no cover - defensive for test environments
    __all__ = []
