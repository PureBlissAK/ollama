"""Orchestrator package for PMO cross-repo orchestration.

Provides lightweight stubs for dependency graph resolution and deployment
plan generation used by higher-level orchestration tasks.
"""

from .graph import DependencyGraph
from .deployment import DeploymentPlan

__all__ = ["DependencyGraph", "DeploymentPlan"]
