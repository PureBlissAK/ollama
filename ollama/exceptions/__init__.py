"""Ollama exception hierarchy."""

from .authentication import AuthenticationError
from .base import OllamaError
from .model import ModelError, ModelLoadError, ModelNotFoundError

__all__ = [
    "AuthenticationError",
    "OllamaError",
    "ModelError",
    "ModelLoadError",
    "ModelNotFoundError",
]
