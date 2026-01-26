"""Webhook handler stubs for alerts."""
from typing import Callable, List


class WebhookHandler:
    """Registerable webhook handler that records alerts (test-friendly)."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[dict], None]] = []
        self._sent: List[dict] = []

    def register(self, fn: Callable[[dict], None]) -> None:
        self._handlers.append(fn)

    def send_alert(self, payload: dict) -> None:
        """Call registered handlers and record the alert payload."""
        self._sent.append(payload)
        for h in list(self._handlers):
            try:
                h(payload)
            except Exception:
                # Do not raise from handlers in tests
                pass

    def sent_alerts(self) -> List[dict]:
        return list(self._sent)
