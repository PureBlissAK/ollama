"""Executive dashboards package for PMO.

Contains Grafana dashboard artifacts and a minimal metrics exporter stub.
"""

from .exporter import MetricsExporter

__all__ = ["MetricsExporter"]
