"""Smart suggestions package for PMO.

Provides a lightweight `SmartSuggestionsEngine` prototype that ranks
candidate suggestions using simple text-overlap heuristics. This is a
dependency-free scaffold suitable for unit tests and iterative improvement.
"""

from .engine import SmartSuggestionsEngine

__all__ = ["SmartSuggestionsEngine"]
