"""
Metrics definitions for Ollama.

Provides Prometheus counters and histograms for request tracking,
response sizing, rate limiting, and cache metrics.
"""

from __future__ import annotations

from typing import Dict

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
	"http_requests_total",
	"Total HTTP requests",
	["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
	"http_request_duration_seconds",
	"HTTP request latency in seconds",
	["method", "endpoint"],
	buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)

REQUEST_SIZE = Histogram(
	"http_request_size_bytes",
	"Size of HTTP requests in bytes",
	["method", "endpoint"],
	buckets=[500, 1_000, 5_000, 10_000, 50_000, 100_000],
)

RESPONSE_SIZE = Histogram(
	"http_response_size_bytes",
	"Size of HTTP responses in bytes",
	["method", "endpoint", "status_code"],
	buckets=[500, 1_000, 5_000, 10_000, 50_000, 100_000],
)

RATE_LIMIT_EXCEEDED = Counter(
	"rate_limit_exceeded_total",
	"Total number of rate limit violations",
	["endpoint"],
)

CACHE_HITS = Counter(
	"cache_hits_total",
	"Total cache hits",
	["cache"],
)

CACHE_MISSES = Counter(
	"cache_misses_total",
	"Total cache misses",
	["cache"],
)


def get_metrics_summary() -> Dict[str, float]:
	"""Provide a simple summary of key counters for quick inspection."""

	return {
		"requests_total": float(REQUEST_COUNT._value.get() if REQUEST_COUNT._value else 0),
		"rate_limit_exceeded_total": float(
			RATE_LIMIT_EXCEEDED._value.get() if RATE_LIMIT_EXCEEDED._value else 0
		),
		"cache_hits_total": float(CACHE_HITS._value.get() if CACHE_HITS._value else 0),
		"cache_misses_total": float(
			CACHE_MISSES._value.get() if CACHE_MISSES._value else 0
		),
	}
