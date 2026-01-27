"""Webhook handler stubs for alerts."""

from typing import Any, Callable, List


class WebhookHandler:
    """Registerable webhook handler that records alerts (test-friendly)."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[dict[str, Any]], None]] = []
        self._sent: List[dict[str, Any]] = []

    def register(self, fn: Callable[[dict[str, Any]], None]) -> None:
        self._handlers.append(fn)

    def send_alert(self, payload: dict[str, Any]) -> None:
        """Call registered handlers and record the alert payload."""
        self._sent.append(payload)
        for h in list(self._handlers):
            try:
                h(payload)
            except Exception:
                # Do not raise from handlers in tests
                pass

    def sent_alerts(self) -> List[dict[str, Any]]:
        return list(self._sent)
