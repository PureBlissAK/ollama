# Cost Optimization Agent

This package provides lightweight discovery and analysis tools for cost
optimization. It is a scaffold designed for unit testing and iterative
enhancement; production code should integrate with cloud billing APIs and
perform safe rightsizing analyses.

Modules:
- `discovery.py`: `discover_resources()` stub and `ResourceSnapshot` dataclass.
- `analysis.py`: `CostAnalyzer` and `CostSavingSuggestion` dataclass.
