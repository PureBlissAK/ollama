import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import the predictive module under its package-qualified name so dataclass resolution works
module_path = Path(__file__).resolve().parents[3] / "ollama" / "pmo" / "predictive_analytics.py"
module_name = "ollama.pmo.predictive_analytics"
spec = importlib.util.spec_from_file_location(module_name, str(module_path))
module = importlib.util.module_from_spec(spec)
# register before executing so dataclass and typing inspect the correct module object
sys.modules[module_name] = module
assert spec and spec.loader
spec.loader.exec_module(module)

PredictiveAnalytics = module.PredictiveAnalytics
ForecastResult = module.ForecastResult


def make_snapshots(n: int, start_score: float = 90.0, decline: float = 0.2):
    now = datetime.utcnow()
    return [(now - timedelta(days=(n - 1 - i)), start_score - i * decline) for i in range(n)]


def test_predict_linear_basic():
    pa = PredictiveAnalytics()
    snaps = make_snapshots(10, start_score=90.0, decline=0.5)
    pa.record_snapshots(snaps)
    res: ForecastResult = pa.predict(days_ahead=7, method="linear")
    assert isinstance(res.predicted_score, float)
    assert 0.0 <= res.predicted_score <= 100.0
    assert res.method == "linear"
    assert 0.0 <= res.confidence <= 1.0


def test_predict_ma_basic():
    pa = PredictiveAnalytics()
    snaps = make_snapshots(5, start_score=80.0, decline=0.1)
    pa.record_snapshots(snaps)
    res = pa.predict(days_ahead=14, method="ma")
    assert res.method == "ma"
    assert abs(res.predicted_score - sum([s for _, s in snaps]) / len(snaps)) <= 1.0


def test_insufficient_snapshots():
    pa = PredictiveAnalytics()
    with pytest.raises(ValueError):
        pa.predict(days_ahead=10)


def test_add_snapshot_and_predict():
    pa = PredictiveAnalytics()
    now = datetime.utcnow()
    pa.add_snapshot(now - timedelta(days=2), 88.0)
    pa.add_snapshot(now - timedelta(days=1), 87.5)
    pa.add_snapshot(now, 87.0)
    res = pa.predict(days_ahead=3)
    assert res.current_score == 87.0
    assert 0.0 <= res.confidence <= 1.0
