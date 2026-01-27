from ollama.pmo.costs.analysis import CostAnalyzer
from ollama.pmo.costs.discovery import discover_resources


def test_discovery_returns_snapshots():
    snaps = discover_resources()
    assert len(snaps) >= 1
    assert all(hasattr(s, "monthly_cost") for s in snaps)


def test_cost_analyzer_suggestions():
    snaps = discover_resources()
    analyzer = CostAnalyzer(snapshots=snaps)
    suggestions = analyzer.generate_savings(top_k=2)
    assert len(suggestions) == 2
    for s in suggestions:
        assert s.estimated_savings <= s.current_monthly
