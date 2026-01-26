# PMO Reporting

This package contains the `AutomatedReportingEngine` used to generate
lightweight weekly summary reports for PMO workflows.

Usage
-----

>>> from ollama.pmo.reporting.cli import run_weekly_summary
>>> run_weekly_summary({"inference_requests": 1234, "errors": 2})

The module is intentionally dependency-free and suitable for scheduled
jobs or simple unit tests. For richer exporters and persistence, extend
the `AutomatedReportingEngine` in future work.
