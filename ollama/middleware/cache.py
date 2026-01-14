"""Response caching middleware - refactored into individual modules.

This module provides backward compatibility by re-exporting from the individual
caching modules. Use the specific modules for new code:
- ollama.middleware.cache_key
- ollama.middleware.caching_middleware
- ollama.middleware.cache_decorator
- ollama.middleware.rate_limiter_cache
- ollama.middleware.cache_stats
"""

# Backward compatibility re-exports
from ollama.middleware.cache_decorator import cache_response
from ollama.middleware.cache_key import CacheKey
from ollama.middleware.cache_stats import CacheStats
from ollama.middleware.caching_middleware import CachingMiddleware
from ollama.middleware.rate_limiter_cache import RateLimiterCache

__all__ = [
    "CacheKey",
    "CacheStats",
    "CachingMiddleware",
    "RateLimiterCache",
    "cache_response",
]
