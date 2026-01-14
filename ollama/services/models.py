"""Ollama model management and integration (backward compatibility).

This module re-exports classes split into individual modules.
For new code, import directly from specific modules.

Legacy imports (deprecated):
    >>> from ollama.services.models import Model, ModelType

Preferred imports:
    >>> from ollama.services.model import Model
    >>> from ollama.services.model_type import ModelType
    >>> from ollama.services.generate_request import GenerateRequest
    >>> from ollama.services.generate_response import GenerateResponse
    >>> from ollama.services.ollama_model_manager import OllamaModelManager
"""

from ollama.services.generate_request import GenerateRequest
from ollama.services.generate_response import GenerateResponse
from ollama.services.model import Model
from ollama.services.model_type import ModelType
from ollama.services.ollama_model_manager import OllamaModelManager

__all__ = [
    "Model",
    "ModelType",
    "GenerateRequest",
    "GenerateResponse",
    "OllamaModelManager",
]
