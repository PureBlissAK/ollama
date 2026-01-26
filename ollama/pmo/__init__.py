"""PMO Package - Elite Program Management Office Automation.

This package provides comprehensive PMO automation for the kushin77 organization.

Modules:
    agent: Core PMO Agent with GitHub/GCP integration
    analyzer: AI-powered repository analysis (v1.1.0)
    classifier: AI-powered issue classification and triage (v1.2.0)
    remediation: Advanced auto-remediation with 15+ fix patterns (NEW in v1.3.0)
    drift_predictor: Predictive drift detection and forecasting (NEW in v1.3.0)
    scheduler: Automated remediation scheduling (cron, event-driven) (NEW in v1.3.0)
    audit: Comprehensive fix history and rollback capability (NEW in v1.3.0)
    cli: Command-line interface for PMO operations
    
Example:
    >>> from ollama.pmo import (
    ...     PMOAgent, RepositoryAnalyzer, IssueClassifier,
    ...     RemediationEngine, DriftPredictor, SchedulerEngine, AuditTrail
    ... )
    >>> 
    >>> # Validate compliance
    >>> agent = PMOAgent(repo="kushin77/ollama")
    >>> agent.validate_compliance()
    >>> 
    >>> # Advanced remediation
    >>> engine = RemediationEngine(repo="kushin77/ollama")
    >>> result = engine.remediate_advanced(severity_threshold='high')
    >>> 
    >>> # Predict future drift
    >>> predictor = DriftPredictor(repo="kushin77/ollama")
    >>> forecast = predictor.predict_drift(days_ahead=30)
    >>> 
    >>> # Schedule automated remediation
    >>> scheduler = SchedulerEngine()
    >>> scheduler.schedule_daily(hour=2, minute=0)
    >>> scheduler.start()
    >>> 
    >>> # Analyze fix effectiveness
    >>> audit = AuditTrail(repo="kushin77/ollama")
    >>> metrics = audit.get_effectiveness_metrics()
"""

"""PMO Package - Elite Program Management Office Automation.

This package exposes domain classes via lazy imports to avoid requiring all
optional runtime dependencies during test discovery or light-weight imports.
"""

from typing import Any
import importlib

__all__ = [
    'PMOAgent',
    'PMOValidationError',
    'RepositoryAnalyzer',
    'IssueClassifier',
    'RemediationEngine',
    'RemediationFix',
    'RemediationResult',
    'DriftPredictor',
    'ComplianceSnapshot',
    'DriftForecast',
    'SchedulerEngine',
    'ScheduledTask',
    'TaskStatus',
    'TriggerType',
    'AuditTrail',
    'AuditEntry',
    'cli',
    'PredictiveAnalytics',
    'ForecastResult',
    'AutomatedReportingEngine',
    'WeeklyReport',
]

__version__ = '1.4.0'

# Mapping from attribute name -> module (under ollama.pmo) where it lives
_EXPORT_MODULE_MAP: dict[str, str] = {
    'PMOAgent': 'agent',
    'PMOValidationError': 'agent',
    'RepositoryAnalyzer': 'analyzer',
    'IssueClassifier': 'classifier',
    'RemediationEngine': 'remediation',
    'RemediationFix': 'remediation',
    'RemediationResult': 'remediation',
    'DriftPredictor': 'drift_predictor',
    'ComplianceSnapshot': 'drift_predictor',
    'DriftForecast': 'drift_predictor',
    'SchedulerEngine': 'scheduler',
    'ScheduledTask': 'scheduler',
    'TaskStatus': 'scheduler',
    'TriggerType': 'scheduler',
    'AuditTrail': 'audit',
    'AuditEntry': 'audit',
    'cli': 'cli',
}

# expose predictive and reporting lazy imports
_EXPORT_MODULE_MAP.update({
    'PredictiveAnalytics': 'predictive_analytics',
    'ForecastResult': 'predictive_analytics',
    'AutomatedReportingEngine': 'reporting.engine',
    'WeeklyReport': 'reporting.engine',
})


def __getattr__(name: str) -> Any:  # lazy import attributes
    module_name = _EXPORT_MODULE_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__} has no attribute {name}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    return getattr(module, name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORT_MODULE_MAP.keys()))
