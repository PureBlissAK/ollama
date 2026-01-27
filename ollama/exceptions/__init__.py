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



# Inference timeout - provided for backward compatibility with tests
class InferenceTimeoutError(OllamaError):
    """Raised when an inference request times out."""

    def __init__(self, elapsed_ms: float, timeout_ms: int) -> None:
        self.elapsed_ms = elapsed_ms
        self.timeout_ms = timeout_ms
        super().__init__(
            code="INFERENCE_TIMEOUT",
            message=f"Inference timed out after {elapsed_ms:.1f}ms (limit: {timeout_ms}ms)",
            status_code=504,
            details={"elapsed_ms": elapsed_ms, "timeout_ms": timeout_ms},
        )


__all__ = [
    "APIKeyInvalidError",
    "AuthenticationError",
    "ModelNotFoundError",
    "OllamaError",
    "OllamaException",
    "RateLimitExceededError",
    "InferenceTimeoutError",
]
