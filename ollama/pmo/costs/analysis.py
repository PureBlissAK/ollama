"""Cost analysis helpers and suggestion generator."""

from dataclasses import dataclass
from typing import List

from .discovery import ResourceSnapshot


@dataclass
class CostSavingSuggestion:
    resource_id: str
    current_monthly: float
    estimated_savings: float
    reason: str


class CostAnalyzer:
    """Analyze resources and propose cost-saving suggestions.

    The implementation is intentionally simple: find the top-N most expensive
    resources and propose rightsizing (50% savings heuristic) as an example.
    """

    def __init__(self, snapshots: List[ResourceSnapshot]):
        self.snapshots = snapshots

    def top_expensive(self, top_k: int = 3) -> List[ResourceSnapshot]:
        return sorted(self.snapshots, key=lambda s: s.monthly_cost, reverse=True)[:top_k]

    def generate_savings(self, top_k: int = 3) -> List[CostSavingSuggestion]:
        suggestions: List[CostSavingSuggestion] = []
        for r in self.top_expensive(top_k=top_k):
            # naive heuristic: propose 50% reduction for rightsizing/spot
            savings = round(r.monthly_cost * 0.5, 2)
            suggestions.append(
                CostSavingSuggestion(
                    resource_id=r.id,
                    current_monthly=r.monthly_cost,
                    estimated_savings=savings,
                    reason="rightsizing/spot-instances",
                )
            )
        return suggestions
