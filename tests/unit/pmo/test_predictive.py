import pytest
from datetime import datetime, timedelta

from ollama.pmo.predictive_analytics import PredictiveAnalytics, ForecastResult


def _make_snapshots(n: int, start_score: float = 90.0, decline: float = 0.2):
    import importlib.util
    from pathlib import Path
    from datetime import datetime, timedelta

    import pytest


    # Import predictive_analytics.py directly to avoid executing package __init__
    module_path = Path(__file__).resolve().parents[3] / "ollama" / "pmo" / "predictive_analytics.py"
    spec = importlib.util.spec_from_file_location("pmo_predictive", str(module_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    import importlib.util
    from pathlib import Path
    from datetime import datetime, timedelta
    import pytest


    # Load `predictive_analytics.py` by path to avoid importing the `ollama` package
    module_path = Path(__file__).resolve().parents[3] / "ollama" / "pmo" / "predictive_analytics.py"
    spec = importlib.util.spec_from_file_location("pmo_predictive", str(module_path))
    module = importlib.util.module_from_spec(spec)
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
        import pytest




