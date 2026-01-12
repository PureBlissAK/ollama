"""Routes package initialization"""
from ollama.api.routes import health, models, generate, chat, embeddings, conversations, documents, usage

__all__ = ["health", "models", "generate", "chat", "embeddings", "conversations", "documents", "usage"]
