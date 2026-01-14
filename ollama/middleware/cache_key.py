"""Generate cache keys for different API endpoints."""

import hashlib


class CacheKey:
    """Generate cache keys for different endpoints."""

    @staticmethod
    def models(model_name: str | None = None) -> str:
        """Cache key for models list or specific model."""
        if model_name:
            return f"models:{model_name}"
        return "models:all"

    @staticmethod
    def generate(model: str, prompt: str) -> str:
        """Cache key for generation requests."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"generate:{model}:{prompt_hash}"

    @staticmethod
    def chat(conversation_id: str) -> str:
        """Cache key for chat conversation."""
        return f"chat:{conversation_id}"

    @staticmethod
    def embeddings(model: str, text: str) -> str:
        """Cache key for embeddings."""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"embeddings:{model}:{text_hash}"

    @staticmethod
    def search(collection: str, query: str) -> str:
        """Cache key for semantic search."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"search:{collection}:{query_hash}"

    @staticmethod
    def user_key(user_id: str, endpoint: str) -> str:
        """Cache key for user-specific data."""
        return f"user:{user_id}:{endpoint}"
