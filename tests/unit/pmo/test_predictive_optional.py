import importlib.util
import sys
from pathlib import Path

import pytest

# Load predictive module under package name so optional integrations work
module_path = Path(__file__).resolve().parents[3] / "ollama" / "pmo" / "predictive_analytics.py"
module_name = "ollama.pmo.predictive_analytics"
if module_name not in sys.modules:
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
else:
    module = sys.modules[module_name]

PredictiveAnalytics = module.PredictiveAnalytics


@pytest.mark.skipif(
    importlib.util.find_spec("statsmodels") is None,
    reason="statsmodels not installed",
)
def test_arima_falls_back_or_runs():
    pa = PredictiveAnalytics()
    now = __import__("datetime").datetime.utcnow()
    snaps = [
        (now, 90.0),
        (now.replace(day=now.day - 1), 89.5),
        (now.replace(day=now.day - 2), 89.0),
    ]
    pa.record_snapshots(list(reversed(snaps)))
    # If statsmodels is present this should run ARIMA path; otherwise fallback to linear
    res = pa.predict(days_ahead=5, method="arima")
    assert hasattr(res, "predicted_score")


@pytest.mark.skipif(
    importlib.util.find_spec("prophet") is None and importlib.util.find_spec("fbprophet") is None,
    reason="prophet not installed",
)
def test_prophet_falls_back_or_runs():
    pa = PredictiveAnalytics()
    now = __import__("datetime").datetime.utcnow()
    snaps = [
        (now, 85.0),
        (now.replace(day=now.day - 1), 84.5),
        (now.replace(day=now.day - 2), 84.0),
        (now.replace(day=now.day - 3), 83.5),
    ]
    pa.record_snapshots(list(reversed(snaps)))
    res = pa.predict(days_ahead=3, method="prophet")
    assert hasattr(res, "predicted_score")
