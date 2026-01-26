"""Cost optimization package for PMO.

Contains lightweight discovery and analysis utilities for tracking and
proposing cost-saving actions. Designed to be dependency-free and testable.
"""

from .discovery import ResourceSnapshot
from .analysis import CostAnalyzer, CostSavingSuggestion

__all__ = ["ResourceSnapshot", "CostAnalyzer", "CostSavingSuggestion"]
