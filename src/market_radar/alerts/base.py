"""Provider-neutral alert delivery interface."""

from typing import Protocol

from market_radar.alerts.message import AlertMessage


class Notifier(Protocol):
    """Deliver formatted alerts to a configured channel."""

    def send(self, message: AlertMessage) -> None:
        """Deliver an alert message."""
