"""Predictive analytics helpers for PMO compliance forecasting.

This module provides a lightweight PredictiveAnalytics class that builds on
`DriftPredictor` snapshots to generate forecasts, simple linear regression
baselines, moving-average forecasts, anomaly detection, and hooks for
ARIMA/Prophet (optional, if installed).

This file is intentionally dependency-light to allow running out-of-the-box.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

_np: Any = None
try:
    import numpy as _np
except Exception:
    _np = None


@dataclass
class ForecastResult:
    current_score: float
    predicted_score: float
    confidence: float  # 0..1
    method: str
    details: Dict[str, Any]


class PredictiveAnalytics:
    """Lightweight predictive analytics for compliance scores.

    Usage:
        pa = PredictiveAnalytics()
        pa.record_snapshots([ (ts1, 87.0), (ts2, 85.5), ... ])
        f = pa.predict(days_ahead=30)
    """

    def __init__(self) -> None:
        self.snapshots: List[tuple[datetime, float]] = []

    def record_snapshots(self, snapshots: List[tuple[datetime, float]]) -> None:
        """Record a list of (timestamp, score) snapshots.

        The snapshots list may be unsorted; it will be sorted by timestamp.
        """
        self.snapshots = sorted(snapshots, key=lambda x: x[0])

    def add_snapshot(self, timestamp: datetime, score: float) -> None:
        """Add a single snapshot."""
        self.snapshots.append((timestamp, score))
        self.snapshots.sort(key=lambda x: x[0])

    def _validate(self) -> None:
        if len(self.snapshots) < 2:
            raise ValueError("At least two snapshots required for prediction")

    def predict(self, days_ahead: int = 30, method: str = "linear") -> ForecastResult:
        """Predict future compliance score `days_ahead` days ahead.

        Supported `method` values:
        - "linear": simple linear regression slope projection
        - "ma": moving average baseline
        - "arima": placeholder for ARIMA (requires statsmodels)
        - "prophet": placeholder for Prophet (requires prophet package)

        Returns a `ForecastResult` with predicted score and confidence.
        """
        self._validate()
        if method == "linear":
            return self._predict_linear(days_ahead)
        if method == "ma":
            return self._predict_ma(days_ahead)
        if method == "arima":
            return self._predict_arima(days_ahead)
        if method == "prophet":
            return self._predict_prophet(days_ahead)
        raise ValueError(f"Unsupported method: {method}")

    def _predict_linear(self, days_ahead: int) -> ForecastResult:
        # Compute linear regression slope (score per day)
        times = [(ts - self.snapshots[0][0]).total_seconds() / 86400.0 for ts, _ in self.snapshots]
        scores = [s for _, s in self.snapshots]
        n = len(times)
        mean_t = sum(times) / n
        mean_s = sum(scores) / n
        num = sum((t - mean_t) * (s - mean_s) for t, s in zip(times, scores, strict=True))
        den = sum((t - mean_t) ** 2 for t in times)
        if den == 0:
            slope = 0.0
        else:
            slope = num / den
        # predict
        predicted = scores[-1] + slope * days_ahead
        predicted = max(0.0, min(100.0, predicted))
        # confidence heuristic: more snapshots and lower volatility -> higher confidence
        vol = _std(scores)
        confidence = _compute_confidence(n, vol)
        details = {"slope_per_day": slope, "volatility": vol, "samples": n}
        return ForecastResult(
            current_score=scores[-1],
            predicted_score=predicted,
            confidence=confidence,
            method="linear",
            details=details,
        )

    def _predict_ma(self, days_ahead: int, window: Optional[int] = None) -> ForecastResult:
        scores = [s for _, s in self.snapshots]
        n = len(scores)
        if window is None:
            window = max(3, min(7, n))
        window = min(window, n)
        ma = sum(scores[-window:]) / window
        predicted = ma  # naive constant forecast
        confidence = _compute_confidence(n, _std(scores)) * 0.75
        details = {"window": window, "ma": ma, "samples": n}
        return ForecastResult(
            current_score=scores[-1],
            predicted_score=predicted,
            confidence=confidence,
            method="ma",
            details=details,
        )

    def _predict_arima(self, days_ahead: int) -> ForecastResult:
        # Placeholder: attempt to use statsmodels if available
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except Exception:
            # fallback to linear
            return self._predict_linear(days_ahead)
        scores = [s for _, s in self.snapshots]
        # auto-tune order for short series
        order = _tune_arima_order(scores)
        model = ARIMA(scores, order=order)
        fitted = model.fit()
        forecast = fitted.forecast(steps=days_ahead)
        predicted = float(forecast[-1])
        predicted = max(0.0, min(100.0, predicted))
        confidence = 0.85
        details = {"model": f"ARIMA{order}", "samples": len(scores)}
        return ForecastResult(
            current_score=scores[-1],
            predicted_score=predicted,
            confidence=confidence,
            method="arima",
            details=details,
        )

    def _predict_prophet(self, days_ahead: int) -> ForecastResult:
        # Placeholder: attempt to use prophet (fbprophet or prophet) if available
        try:
            from prophet import Prophet
        except Exception:
            return self._predict_linear(days_ahead)
        df = _to_prophet_df(self.snapshots)
        m = Prophet()
        m.fit(df)
        future = m.make_future_dataframe(periods=days_ahead)
        fc = m.predict(future)
        predicted = float(fc.iloc[-1]["yhat"])
        predicted = max(0.0, min(100.0, predicted))
        confidence = 0.88
        details = {"model": "Prophet"}
        return ForecastResult(
            current_score=self.snapshots[-1][1],
            predicted_score=predicted,
            confidence=confidence,
            method="prophet",
            details=details,
        )


# Helper functions


def _std(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(var)


def _compute_confidence(n: int, volatility: float) -> float:
    # Heuristic: more samples and lower volatility increase confidence
    base = min(0.95, 0.2 + 0.15 * n)
    vol_penalty = min(0.8, volatility / 20.0)
    conf = max(0.1, base * (1.0 - vol_penalty))
    return round(conf, 3)


def _to_prophet_df(snapshots: List[tuple[datetime, float]]) -> Any:
    # convert to pandas DataFrame for Prophet
    import pandas as pd

    df = pd.DataFrame([(ts, s) for ts, s in snapshots], columns=["ds", "y"])
    return df


def _tune_arima_order(
    values: List[float], max_p: int = 2, max_d: int = 1, max_q: int = 2
) -> tuple[int, int, int]:
    """Simple grid search to pick ARIMA(p,d,q) with lowest AIC for short series.

    Returns an order tuple. If tuning fails, returns default (1,1,0).
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except Exception:
        return (1, 1, 0)

    best_order = (1, 1, 0)
    best_aic = float("inf")
    for p in range(0, max_p + 1):
        for d in range(0, max_d + 1):
            for q in range(0, max_q + 1):
                try:
                    model = ARIMA(values, order=(p, d, q))
                    res = model.fit(method="statespace", disp=0)
                    aic = float(getattr(res, "aic", float("inf")))
                    if aic < best_aic:
                        best_aic = aic
                        best_order = (p, d, q)
                except Exception:
                    continue
    return best_order
