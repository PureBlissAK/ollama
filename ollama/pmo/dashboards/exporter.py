"""Minimal metrics exporter stub for executive dashboards.

This module provides a lightweight `MetricsExporter` class that exposes
an interface for registering metrics and returning a Prometheus-compatible
text exposition. It is intentionally minimal and dependency-free so it can
be used in unit tests and as a starting point for production exporters.
"""


class MetricsExporter:
    """Simple in-memory metrics registry and exporter."""

    def __init__(self) -> None:
        self._metrics: dict[str, float] = {}

    def set_metric(self, name: str, value: float) -> None:
        self._metrics[name] = float(value)

    def get_metric(self, name: str) -> float:
        return self._metrics.get(name, 0.0)

    def export_text(self) -> str:
        """Return a simple Prometheus-style text exposition."""
        lines = []
        for k, v in sorted(self._metrics.items()):
            lines.append(f"# HELP {k} Auto-generated metric")
            lines.append(f"# TYPE {k} gauge")
            lines.append(f"{k} {v}")
        return "\n".join(lines)
