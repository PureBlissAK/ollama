"""Routes package initialization"""
from ollama.api.routes import health, models, generate, chat, embeddings

__all__ = ["health", "models", "generate", "chat", "embeddings"]
