# Executive Dashboards

This folder contains artifacts for executive dashboards (Grafana) and a
minimal `MetricsExporter` stub used to produce metrics for dashboards and
tests.

Files:

- `grafana/executive_dashboard.json`: Example Grafana dashboard JSON.
- `exporter.py`: Minimal in-memory metrics exporter with Prometheus-style
  text exposition.

Usage example:

> > > from ollama.pmo.dashboards import MetricsExporter
> > > e = MetricsExporter()
> > > e.set_metric('pmo_compliance_score', 92.5)
> > > print(e.export_text())
