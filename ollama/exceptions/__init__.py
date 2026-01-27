"""Exception hierarchy.

This module exposes the canonical exception types and provides a small set
of backward-compatible aliases expected by older code and tests.
"""

from .impl.base import AuthenticationError, OllamaError
from .impl.model import ModelNotFoundError

# Backwards-compatible aliases
# Older callers expect `OllamaException` as the base name; keep alias.
OllamaException = OllamaError

# Authentication-related aliases
APIKeyInvalidError = AuthenticationError


# Rate limiting error - not present in older impls, provide a simple class
class RateLimitExceededError(OllamaError):
    """Raised when a client exceeds allowed rate limits."""


__all__ = [
    "APIKeyInvalidError",
    "AuthenticationError",
    "ModelNotFoundError",
    "OllamaError",
    "OllamaException",
    "RateLimitExceededError",
]
