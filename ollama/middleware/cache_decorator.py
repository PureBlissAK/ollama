"""Decorator for caching endpoint responses."""

import json
import logging
from collections.abc import Callable
from functools import wraps

from ollama.services import CacheManager

logger = logging.getLogger(__name__)


async def cache_response(key: str, ttl: int = 3600, cache_manager: "CacheManager | None" = None):
    """Decorator for caching endpoint responses.

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
