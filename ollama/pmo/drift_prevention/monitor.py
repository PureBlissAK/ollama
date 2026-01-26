"""Monitoring loop for compliance drift detection."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Any, List


@dataclass
class DriftEvent:
    timestamp: datetime
    metric: str
    value: float
    note: str


class MonitoringLoop:
    """Simple monitoring loop that runs checks and emits DriftEvent via handler.

    The loop is intentionally synchronous and test-friendly. For production
    it can be scheduled or run in an async worker.
    """

    def __init__(self, check_fn: Callable[[], Dict[str, float]], handler: Callable[[DriftEvent], None]):
        """Initialize with a `check_fn` that returns latest metrics and a `handler`.

        Args:
            check_fn: callable returning mapping metric -> numeric value.
            handler: callable accepting a DriftEvent when a drift is detected.
        """
        self.check_fn = check_fn
        self.handler = handler

    def run_once(self) -> List[DriftEvent]:
        """Run one monitoring iteration and return any detected DriftEvents.

        Detection logic: a very light heuristic — if any metric is negative
        or zero (when it is expected positive) we treat as drift for tests.
        """
        metrics = self.check_fn()
        events: List[DriftEvent] = []
        now = datetime.utcnow()
        for k, v in metrics.items():
            if v <= 0:
                ev = DriftEvent(timestamp=now, metric=k, value=v, note="non-positive metric")
                events.append(ev)
                try:
                    self.handler(ev)
                except Exception:
                    # handler errors should not break monitoring; swallow for tests
                    pass
        return events
