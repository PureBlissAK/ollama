"""Routes package initialization"""

from ollama.api.routes import (
    chat,
    conversations,
    documents,
    embeddings,
    generate,
    health,
    models,
    usage,
)

__all__ = [
    "health",
    "models",
    "generate",
    "chat",
    "embeddings",
    "conversations",
    "documents",
    "usage",
]
