from datetime import datetime

from ollama.pmo.drift_prevention.monitor import MonitoringLoop
from ollama.pmo.drift_prevention.webhooks import WebhookHandler
from ollama.pmo.drift_prevention.predictive_adapter import get_forecast_if_available


def test_monitor_detects_non_positive_and_sends_alert():
    metrics = {"pmo_compliance_score": -1.0, "requests": 10}

    def check_fn():
        return metrics

    sent = []

    def handler(ev):
        sent.append(ev.metric)

    loop = MonitoringLoop(check_fn=check_fn, handler=handler)
    events = loop.run_once()
    assert len(events) == 1
    assert sent == ["pmo_compliance_score"]


def test_webhook_handler_records_alerts():
    w = WebhookHandler()
    recorded = []

    def rec(payload):
        recorded.append(payload)

    w.register(rec)
    w.send_alert({"metric": "x", "value": 0})
    assert w.sent_alerts()
    assert recorded[0]["metric"] == "x"


def test_predictive_adapter_returns_none_when_missing():
    # If PredictiveAnalytics is not available in environment, adapter returns None
    # This test just calls the function to ensure it doesn't raise.
    res = get_forecast_if_available(snapshots=[(datetime.utcnow(), 90.0)], days_ahead=3)
    # res may be None or a dict depending on optional deps; assert no exception
    assert res is None or isinstance(res, dict)
