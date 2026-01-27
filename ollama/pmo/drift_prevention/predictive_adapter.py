"""Adapter to call PredictiveAnalytics if available."""

from typing import Any, List, Optional, Tuple


def get_forecast_if_available(
    snapshots: List[Tuple[Any, ...]], days_ahead: int = 7
) -> Optional[dict[str, Any]]:
    """Return a minimal forecast dict if PredictiveAnalytics is available.

    If the predictive module is not importable, return None.
    """
    try:
        # import via package-level lazy exports
        from ollama.pmo import PredictiveAnalytics
    except Exception:
        return None

    try:
        pa = PredictiveAnalytics()
        pa.record_snapshots(snapshots)
        res = pa.predict(days_ahead=days_ahead, method="linear")
        return {
            "predicted_score": res.predicted_score,
            "confidence": res.confidence,
            "method": res.method,
        }
    except Exception:
        return None
