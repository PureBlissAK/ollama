from ollama.pmo.dashboards.exporter import MetricsExporter


def test_metrics_exporter_basic():
    exp = MetricsExporter()
    exp.set_metric("pmo_compliance_score", 88.0)
    exp.set_metric("pmo_inference_requests_total", 1234)
    out = exp.export_text()
    assert "pmo_compliance_score 88.0" in out
    assert "pmo_inference_requests_total 1234.0" in out
