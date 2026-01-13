"""
Metrics Collection Middleware
Collects HTTP and business metrics for monitoring
"""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ollama.metrics import (
    RATE_LIMIT_EXCEEDED,
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_SIZE,
    RESPONSE_SIZE,
)

logger = logging.getLogger(__name__)


class MetricsCollectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting HTTP metrics

    Tracks:
    - Request count by method/endpoint/status
    - Request duration
    - Request/response size
    - Rate limit violations
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize metrics middleware

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> any:
        """
        Process request and collect metrics

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with metrics collected
        """
        # Get request details
        method = request.method
        endpoint = request.url.path

        # Calculate request size
        request_size = 0
        if request.headers:
            request_size = sum(len(f"{k}: {v}".encode()) for k, v in request.headers.items())

        # Measure request processing time
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Collect metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(request_size)

            # Calculate response size
            response_size = response.headers.get("content-length")
            if response_size:
                RESPONSE_SIZE.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).observe(int(response_size))

            # Track rate limit violations
            if status_code == 429:
                RATE_LIMIT_EXCEEDED.labels(endpoint=endpoint).inc()

            return response

        except Exception as e:
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=500).inc()
            logger.error(f"Request error: {e}")
            raise


def setup_metrics_endpoints(app):
    """
    Setup metrics and health check endpoints

    Args:
        app: FastAPI application
    """
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    # Prometheus metrics endpoint - return metrics as direct response
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Get Prometheus metrics in text format"""
        metrics_data = generate_latest()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

    # Metrics summary endpoint
    @app.get("/api/v1/metrics/summary")
    async def metrics_summary():
        """Get metrics summary"""
        from ollama.metrics import get_metrics_summary

        return get_metrics_summary()

    logger.info("✅ Metrics endpoints registered")
