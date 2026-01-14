"""Model type enumeration for Ollama models."""

from enum import Enum


class ModelType(str, Enum):
    """Types of available Ollama models."""

    TEXT_GENERATION = "text_generation"
    EMBEDDING = "embedding"
    CHAT = "chat"
