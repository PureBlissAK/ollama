"""Cost optimization package for PMO.

Contains lightweight discovery and analysis utilities for tracking and
proposing cost-saving actions. Designed to be dependency-free and testable.
"""

from .analysis import CostAnalyzer, CostSavingSuggestion
from .discovery import ResourceSnapshot

__all__ = ["CostAnalyzer", "CostSavingSuggestion", "ResourceSnapshot"]
