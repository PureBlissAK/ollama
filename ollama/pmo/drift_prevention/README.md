# Compliance Drift Prevention

This package contains minimal, dependency-free scaffolding for compliance
drift detection and alerting. It is intentionally small so it can be
unit-tested without optional ML dependencies.

Components:

- `MonitoringLoop` — runs checks and emits `DriftEvent` when a metric is
  non-positive (test heuristic).
- `WebhookHandler` — records sent alerts and invokes registered handlers.
- `PredictiveAdapter` — lightweight adapter that calls `PredictiveAnalytics`
  when available; otherwise it safely returns `None`.
