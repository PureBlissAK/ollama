"""
Response Caching Middleware - Redis-based caching for API responses
Improves performance and reduces database load for frequently accessed data
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ollama.services import CacheManager

logger = logging.getLogger(__name__)


class CacheKey:
    """Generate cache keys for different endpoints"""

    @staticmethod
    def models(model_name: Optional[str] = None) -> str:
        """Cache key for models list or specific model"""
        if model_name:
            return f"models:{model_name}"
        return "models:all"

    @staticmethod
    def generate(model: str, prompt: str) -> str:
        """Cache key for generation requests"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"generate:{model}:{prompt_hash}"

    @staticmethod
    def chat(conversation_id: str) -> str:
        """Cache key for chat conversation"""
        return f"chat:{conversation_id}"

    @staticmethod
    def embeddings(model: str, text: str) -> str:
        """Cache key for embeddings"""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"embeddings:{model}:{text_hash}"

    @staticmethod
    def search(collection: str, query: str) -> str:
        """Cache key for semantic search"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"search:{collection}:{query_hash}"

    @staticmethod
    def user_key(user_id: str, endpoint: str) -> str:
        """Cache key for user-specific data"""
        return f"user:{user_id}:{endpoint}"


class CachingMiddleware(BaseHTTPMiddleware):
    """Middleware for caching GET requests and safe endpoints"""

    CACHEABLE_ENDPOINTS = {
        "/health": 3600,  # 1 hour
        "/api/v1/models": 3600,  # 1 hour
        "/api/v1/models/": 3600,  # Model details
        "/metrics": 60,  # 1 minute
    }

    def __init__(self, app, cache_manager: CacheManager):
        super().__init__(app)
        self.cache_manager = cache_manager

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Cache GET requests to specific endpoints"""

        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Check if endpoint is cacheable
        path = request.url.path
        ttl = None
        for endpoint, endpoint_ttl in self.CACHEABLE_ENDPOINTS.items():
            if path.startswith(endpoint):
                ttl = endpoint_ttl
                break

        if ttl is None:
            return await call_next(request)

        # Generate cache key
        cache_key = f"http:{request.method}:{path}"
        if request.url.query:
            cache_key += f"?{request.url.query}"

        # Try to get from cache
        cached = await self.cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT: {cache_key}")
            return Response(
                content=cached, media_type="application/json", headers={"X-Cache": "HIT"}
            )

        # Call endpoint
        response = await call_next(request)

        # Cache if successful
        if response.status_code == 200:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Store in cache
                await self.cache_manager.set(cache_key, body.decode(), ttl=ttl)
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")

                # Return response with cache header
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers={**dict(response.headers), "X-Cache": "MISS"},
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")
                return response

        return response


async def cache_response(key: str, ttl: int = 3600, cache_manager: Optional[CacheManager] = None):
    """
    Decorator for caching endpoint responses

    Usage:
    @app.get("/api/endpoint")
    @cache_response(key="endpoint_cache", ttl=1800)
    async def my_endpoint():
        return {"data": "value"}
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if cache_manager is None:
                return await func(*args, **kwargs)

            # Try cache
            cached = await cache_manager.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                await cache_manager.set(key, json.dumps(result), ttl=ttl)
                logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Failed to cache: {e}")

            return result

        return wrapper

    return decorator


class RateLimiter:
    """Rate limiting using Redis counters"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    async def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """Check if request is within rate limit"""
        counter_key = f"rate:{key}"

        count = await self.cache_manager.increment(counter_key, 1)

        # Set expiration on first increment
        if count == 1:
            await self.cache_manager.client.expire(counter_key, window)

        return count <= limit

    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests in current window"""
        counter_key = f"rate:{key}"
        current = await self.cache_manager.client.get(counter_key)
        count = int(current) if current else 0
        return max(0, limit - count)


class CacheStats:
    """Track cache performance statistics"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    async def record_hit(self, key: str):
        """Record cache hit"""
        stats_key = f"stats:hits:{key}"
        await self.cache_manager.increment(stats_key, 1)
        await self.cache_manager.client.expire(stats_key, 86400)  # 24h

    async def record_miss(self, key: str):
        """Record cache miss"""
        stats_key = f"stats:misses:{key}"
        await self.cache_manager.increment(stats_key, 1)
        await self.cache_manager.client.expire(stats_key, 86400)  # 24h

    async def get_stats(self, key: str) -> dict:
        """Get cache statistics for a key"""
        hits_key = f"stats:hits:{key}"
        misses_key = f"stats:misses:{key}"

        hits = await self.cache_manager.client.get(hits_key)
        misses = await self.cache_manager.client.get(misses_key)

        hits = int(hits) if hits else 0
        misses = int(misses) if misses else 0
        total = hits + misses

        hit_rate = (hits / total * 100) if total > 0 else 0

        return {"hits": hits, "misses": misses, "total": total, "hit_rate": f"{hit_rate:.2f}%"}
