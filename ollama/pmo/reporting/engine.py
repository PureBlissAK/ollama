"""Automated reporting engine for PMO.

Simple, dependency-free reporting utilities used by CI and local jobs.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List


@dataclass
class WeeklyReport:
    start_date: date
    end_date: date
    metrics: Dict[str, float]
    summary: str


class AutomatedReportingEngine:
    """Generate simple automated reports from metrics.

    This implementation is intentionally minimal: it accepts a mapping of
    metric names to numeric values and produces a short text summary and
    a WeeklyReport dataclass. It is easy to extend with persistence,
    exporters, or richer aggregation logic in follow-ups.
    """

    def generate_weekly_report(self, start: date, end: date, metrics: Dict[str, float]) -> WeeklyReport:
        """Create a WeeklyReport summarizing provided metrics.

        Args:
            start: start date of the reporting window.
            end: end date of the reporting window.
            metrics: mapping metric_name -> numeric value.

        Returns:
            WeeklyReport with a one-paragraph human-readable summary.
        """
        if not metrics:
            summary = "No metrics reported for this period."
        else:
            lines: List[str] = []
            # Top 3 metrics by absolute value
            top = sorted(metrics.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
            for name, val in top:
                lines.append(f"{name}: {val}")
            avg = sum(metrics.values()) / len(metrics)
            lines.append(f"Average (reported metrics): {avg:.2f}")
            summary = "; ".join(lines)

        return WeeklyReport(start_date=start, end_date=end, metrics=metrics, summary=summary)
