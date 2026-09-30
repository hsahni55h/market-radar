"""Logging setup for the application."""

import logging


def configure_logging(log_level: str) -> None:
    """Configure application logging with a consistent console format."""
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # httpx/httpcore log request URLs at INFO, which would leak the Discord webhook.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
