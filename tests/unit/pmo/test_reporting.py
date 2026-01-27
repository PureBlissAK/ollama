from datetime import date

from ollama.pmo.reporting.engine import AutomatedReportingEngine


def test_generate_weekly_report_empty():
    engine = AutomatedReportingEngine()
    rpt = engine.generate_weekly_report(start=date(2026, 1, 1), end=date(2026, 1, 7), metrics={})
    assert rpt.summary == "No metrics reported for this period."


def test_generate_weekly_report_basic():
    engine = AutomatedReportingEngine()
    metrics = {"a": 10, "b": -5, "c": 3}
    rpt = engine.generate_weekly_report(
        start=date(2026, 1, 1), end=date(2026, 1, 7), metrics=metrics
    )
    assert "a: 10" in rpt.summary
    assert "Average (reported metrics)" in rpt.summary
