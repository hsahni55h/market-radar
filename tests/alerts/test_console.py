"""Tests for console alert delivery."""

import logging

import pytest

from market_radar.alerts.console import ConsoleNotifier
from market_radar.alerts.message import AlertMessage, AlertSection


def test_console_notifier_logs_message(caplog: pytest.LogCaptureFixture) -> None:
    """Dry-run delivery writes all message components to the application log."""
    message = AlertMessage(
        title="Nifty 500 Market Movers",
        sections=(AlertSection("Top Gainers", ("GAIN: Rs. 100.00 (+1.00%)",)),),
        footer="Scanned: 1 | Skipped: 0",
        timestamp=None,
    )

    with caplog.at_level(logging.INFO):
        ConsoleNotifier().send(message)

    assert "Nifty 500 Market Movers" in caplog.text
    assert "Top Gainers:" in caplog.text
    assert "GAIN: Rs. 100.00 (+1.00%)" in caplog.text
    assert "Scanned: 1 | Skipped: 0" in caplog.text
