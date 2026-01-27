"""Orchestrator package for PMO cross-repo orchestration.

Provides lightweight stubs for dependency graph resolution and deployment
plan generation used by higher-level orchestration tasks.
"""

from .deployment import DeploymentPlan
from .graph import DependencyGraph

__all__ = ["DependencyGraph", "DeploymentPlan"]
