"""CLI helpers for PMO automated reporting tasks.

Provides a small programmatic entrypoint used by scheduled jobs or tests.
"""
from datetime import date, timedelta
from typing import Dict

from .engine import AutomatedReportingEngine


def run_weekly_summary(metrics: Dict[str, float]) -> dict:
    """Run a weekly summary for the previous 7 days.

    Returns a serializable dict representing the WeeklyReport.
    """
    today = date.today()
    start = today - timedelta(days=7)
    engine = AutomatedReportingEngine()
    report = engine.generate_weekly_report(start=start, end=today, metrics=metrics)
    return {
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "metrics": report.metrics,
        "summary": report.summary,
    }
