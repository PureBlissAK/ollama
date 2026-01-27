"""PMO Package - Elite Program Management Office Automation.

This package provides PMO automation helpers and exposes core classes via lazy
imports so that optional heavy runtime dependencies (GitHub/GCP SDKs, ML
libraries) do not need to be importable during lightweight test discovery.

Public symbols are exported via `__all__` and resolved lazily using
`__getattr__` to keep import-time cost minimal.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "PMOAgent",
    "PMOValidationError",
    "RepositoryAnalyzer",
    "IssueClassifier",
    "RemediationEngine",
    "RemediationFix",
    "RemediationResult",
    "DriftPredictor",
    "ComplianceSnapshot",
    "DriftForecast",
    "SchedulerEngine",
    "ScheduledTask",
    "TaskStatus",
    "TriggerType",
    "AuditTrail",
    "AuditEntry",
    "cli",
    "PredictiveAnalytics",
    "ForecastResult",
    "AutomatedReportingEngine",
    "WeeklyReport",
]

__version__ = "1.4.0"

# Mapping from attribute name -> module (under ollama.pmo) where it lives
_EXPORT_MODULE_MAP: dict[str, str] = {
    "PMOAgent": "agent",
    "PMOValidationError": "agent",
    "RepositoryAnalyzer": "analyzer",
    "IssueClassifier": "classifier",
    "RemediationEngine": "remediation",
    "RemediationFix": "remediation",
    "RemediationResult": "remediation",
    "DriftPredictor": "drift_predictor",
    "ComplianceSnapshot": "drift_predictor",
    "DriftForecast": "drift_predictor",
    "SchedulerEngine": "scheduler",
    "ScheduledTask": "scheduler",
    "TaskStatus": "scheduler",
    "TriggerType": "scheduler",
    "AuditTrail": "audit",
    "AuditEntry": "audit",
    "cli": "cli",
}

# expose predictive and reporting lazy imports
_EXPORT_MODULE_MAP.update(
    {
        "PredictiveAnalytics": "predictive_analytics",
        "ForecastResult": "predictive_analytics",
        "AutomatedReportingEngine": "reporting.engine",
        "WeeklyReport": "reporting.engine",
    }
)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULE_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__} has no attribute {name}")
    module = import_module(f"{__name__}.{module_name}")
    return getattr(module, name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORT_MODULE_MAP.keys()))
