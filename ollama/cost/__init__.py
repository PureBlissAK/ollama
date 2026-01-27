"""Compatibility shim exposing legacy `cost` package symbols.

This module re-exports the implementations from `ollama.services.cost` so
older imports like `from cost.collector import GCPCostCollector` keep working
when the package is used from the repository layout used in tests.
"""

from ollama.services.cost.collector import (
    GCPCostCollector,
    CostSample,
    CostSnapshot,
    CostCategory,
    ResourceMetric,
)

from ollama.services.cost.service import CostManagementService

# Re-export names for `from cost import ...` style
__all__ = [
    "GCPCostCollector",
    "CostSample",
    "CostSnapshot",
    "CostCategory",
    "ResourceMetric",
    "CostManagementService",
]
