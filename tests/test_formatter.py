"""Tests for scan-result alert formatting."""

from datetime import UTC, datetime

from market_radar.formatter import format_scan
from market_radar.scanner import Mover, ScanResult


def test_format_scan_builds_ist_market_movers_message() -> None:
    """A populated result becomes readable gainers and losers sections."""
    result = ScanResult(
        gainers=(Mover("GAIN", 1_234.5, 1_000, 23.45),),
        losers=(Mover("LOSS", 800, 1_000, -20),),
        scanned_count=499,
        skipped_count=2,
        as_of=datetime(2026, 9, 30, 10, 15, tzinfo=UTC),
    )

    message = format_scan(result)

    assert message.title == "Nifty 500 Market Movers"
    assert message.sections[0].heading == "Top Gainers"
    assert message.sections[0].lines == ("GAIN: Rs. 1,234.50 (+23.45%)",)
    assert message.sections[1].heading == "Top Losers"
    assert message.sections[1].lines == ("LOSS: Rs. 800.00 (-20.00%)",)
    assert message.footer == "Scanned: 499 | Skipped: 2"
    assert message.timestamp is not None
    assert message.timestamp == datetime(2026, 9, 30, 15, 45, tzinfo=message.timestamp.tzinfo)
    offset = message.timestamp.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 19_800


def test_format_scan_handles_empty_lists_and_missing_timestamp() -> None:
    """Empty movement lists and timestamps remain displayable."""
    result = ScanResult(
        gainers=(),
        losers=(),
        scanned_count=0,
        skipped_count=3,
        as_of=None,
    )

    message = format_scan(result)

    assert message.sections[0].lines == ("No gainers today.",)
    assert message.sections[1].lines == ("No losers today.",)
    assert message.timestamp is None
