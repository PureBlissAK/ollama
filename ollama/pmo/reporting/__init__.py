"""Reporting package for PMO: automated reports and report generators.

This package provides a lightweight scaffold for automated reporting engines
used by the PMO agent. It contains the `AutomatedReportingEngine` which
generates simple weekly summaries from metric dictionaries.
"""

from .engine import AutomatedReportingEngine, WeeklyReport

__all__ = ["AutomatedReportingEngine", "WeeklyReport"]
