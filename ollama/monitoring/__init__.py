"""Monitoring domain."""

from .impl.jaeger_config import init_jaeger
from .impl.metrics import (
    AUTH_ATTEMPTS,
    CACHE_HITS,
    CACHE_MISSES,
    OLLAMA_TOKENS_GENERATED,
    RATE_LIMIT_EXCEEDED,
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_SIZE,
    RESPONSE_SIZE,
    export_metrics,
    generate_latest,
    get_metrics_summary,
)
from .impl.metrics_middleware import MetricsCollectionMiddleware, setup_metrics_endpoints

__all__ = [
    "setup_metrics_endpoints",
    "MetricsCollectionMiddleware",
    "init_jaeger",
    "AUTH_ATTEMPTS",
    "CACHE_HITS",
    "CACHE_MISSES",
    "OLLAMA_TOKENS_GENERATED",
    "RATE_LIMIT_EXCEEDED",
    "REQUEST_COUNT",
    "REQUEST_DURATION",
    "REQUEST_SIZE",
    "RESPONSE_SIZE",
    "export_metrics",
    "generate_latest",
    "get_metrics_summary",
]
