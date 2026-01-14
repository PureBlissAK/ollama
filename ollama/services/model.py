"""Ollama model data structures."""

from dataclasses import dataclass

from ollama.services.model_type import ModelType


@dataclass
class Model:
    """Represents an available Ollama model."""

    name: str
    """Model identifier (e.g., 'llama2:latest', 'mistral:7b')"""

    size: str
    """Model size in human-readable format (e.g., '3.8GB')"""

    model_type: ModelType
    """Type of model (text generation, embedding, etc.)"""

    description: str
    """Human-friendly model description"""

    parameters: int
    """Number of parameters in the model"""

    context_length: int
    """Context window size in tokens"""

    quantization: str
    """Quantization level (e.g., '4bit', '8bit', 'float16')"""

    loaded: bool = False
    """Whether model is currently loaded in memory"""
