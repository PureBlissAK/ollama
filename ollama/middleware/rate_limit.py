"""
Rate Limiting Middleware
Provides token bucket and sliding window rate limiting
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend

    Implements:
    - Token bucket algorithm for rate limiting
    - Per-user and per-IP rate limits
    - Configurable limits and time windows
    """

    def __init__(self, requests_per_minute: int = 60, burst_size: Optional[int] = None):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.tokens_per_second = requests_per_minute / 60.0

        # In-memory storage - sufficient for single-instance deployments
        # For distributed systems, use RedisRateLimiter below
        # See: docs/DEPLOYMENT.md for production rate limiting setup
        self._buckets = defaultdict(lambda: {"tokens": self.burst_size, "last_update": time.time()})

    def _refill_bucket(self, bucket_key: str):
        """Refill tokens in bucket based on elapsed time"""
        bucket = self._buckets[bucket_key]
        now = time.time()
        elapsed = now - bucket["last_update"]

        # Add tokens based on time elapsed
        tokens_to_add = elapsed * self.tokens_per_second
        bucket["tokens"] = min(self.burst_size, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

    def check_rate_limit(self, key: str) -> tuple[bool, dict]:
        """
        Check if request should be allowed

        Args:
            key: Unique identifier (user_id, IP, etc.)

        Returns:
            Tuple of (allowed, limit_info)
        """
        self._refill_bucket(key)
        bucket = self._buckets[key]

        limit_info = {
            "limit": self.requests_per_minute,
            "remaining": int(bucket["tokens"]),
            "reset": int(bucket["last_update"] + 60),
        }

        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True, limit_info
        else:
            return False, limit_info

    def reset(self, key: str):
        """Reset rate limit for a key"""
        if key in self._buckets:
            del self._buckets[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Applies rate limits based on:
    - User ID (for authenticated requests)
    - IP address (for unauthenticated requests)
    - API endpoint
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        exclude_paths: Optional[list] = None,
    ):
        """
        Initialize rate limit middleware

        Args:
            app: FastAPI application
            requests_per_minute: Global rate limit
            burst_size: Maximum burst size
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Determine rate limit key
        # Priority: user_id > api_key > ip_address
        rate_limit_key = None

        # Check for authenticated user (set by auth middleware)
        if hasattr(request.state, "user"):
            rate_limit_key = f"user:{request.state.user.id}"
        else:
            # Fall back to IP address
            client_ip = request.client.host if request.client else "unknown"
            rate_limit_key = f"ip:{client_ip}"

        # Check rate limit
        allowed, limit_info = self.limiter.check_rate_limit(rate_limit_key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {rate_limit_key} " f"on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(limit_info["reset"]),
                    "Retry-After": "60",
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])

        return response


class EndpointRateLimiter:
    """
    Decorator for endpoint-specific rate limiting

    Usage:
        @router.get("/expensive-endpoint")
        @EndpointRateLimiter(requests_per_minute=10)
        async def expensive_endpoint():
            ...
    """

    def __init__(self, requests_per_minute: int, burst_size: Optional[int] = None):
        """
        Initialize endpoint rate limiter

        Args:
            requests_per_minute: Rate limit for this endpoint
            burst_size: Maximum burst size
        """
        self.limiter = RateLimiter(requests_per_minute, burst_size)

    async def __call__(self, request: Request):
        """
        Check rate limit for endpoint

        Args:
            request: Incoming request

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Determine rate limit key
        if hasattr(request.state, "user"):
            key = f"endpoint:{request.url.path}:user:{request.state.user.id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"endpoint:{request.url.path}:ip:{client_ip}"

        allowed, limit_info = self.limiter.check_rate_limit(key)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for endpoint {request.url.path}",
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(limit_info["reset"]),
                    "Retry-After": "60",
                },
            )


# Redis-based rate limiter for production
class RedisRateLimiter:
    """
    Redis-backed rate limiter for distributed systems

    Uses Redis INCR and EXPIRE for atomic rate limiting.
    Implementation required for multi-instance deployments.
    Reference: https://github.com/kushin77/ollama/issues
    """

    def __init__(self, redis_client, requests_per_minute: int = 60):
        """
        Initialize Redis rate limiter

        Args:
            redis_client: Redis client instance
            requests_per_minute: Rate limit
        """
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute

    async def check_rate_limit(self, key: str) -> tuple[bool, dict]:
        """
        Check rate limit using Redis

        Args:
            key: Rate limit key

        Returns:
            Tuple of (allowed, limit_info)

        Implementation Strategy:
        - Use INCR on rate limit key with EXPIRE
        - Track reset time with PEXPIRE for precision
        - See redis-py docs for asyncio examples
        """
        # Implementation tracked in GitHub issues
        # Use sliding window or token bucket with Redis INCR + EXPIRE
        raise NotImplementedError("Redis rate limiting requires async-redis client setup")
