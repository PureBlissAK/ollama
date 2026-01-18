"""Exception hierarchy."""

from .impl.base import AuthenticationError, OllamaError
from .impl.model import ModelNotFoundError

__all__ = [
    "OllamaError",
    "AuthenticationError",
    "ModelNotFoundError",
]
