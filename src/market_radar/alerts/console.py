"""Console-oriented alert notifier for dry runs."""

import logging

from market_radar.alerts.message import AlertMessage

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    """Log alert messages rather than delivering them externally."""

    def send(self, message: AlertMessage) -> None:
        """Log a readable rendering of an alert message."""
        sections = "\n".join(
            f"{section.heading}:\n" + "\n".join(section.lines) for section in message.sections
        )
        timestamp = message.timestamp.isoformat() if message.timestamp is not None else "unknown"
        logger.info("%s\n%s\n%s\n%s", message.title, sections, message.footer, timestamp)
