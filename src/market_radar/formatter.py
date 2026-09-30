"""Pure formatting of scan results into delivery-neutral messages."""

from zoneinfo import ZoneInfo

from market_radar.alerts.message import AlertMessage, AlertSection
from market_radar.scanner import Mover, ScanResult

IST = ZoneInfo("Asia/Kolkata")


def format_scan(result: ScanResult) -> AlertMessage:
    """Format a scan result as a concise market-movers alert."""
    timestamp = result.as_of.astimezone(IST) if result.as_of is not None else None
    return AlertMessage(
        title="Nifty 500 Market Movers",
        sections=(
            AlertSection("Top Gainers", _format_movers(result.gainers, "No gainers today.")),
            AlertSection("Top Losers", _format_movers(result.losers, "No losers today.")),
        ),
        footer=f"Scanned: {result.scanned_count} | Skipped: {result.skipped_count}",
        timestamp=timestamp,
    )


def format_low_data_warning(result: ScanResult, expected_count: int) -> AlertMessage:
    """Format a warning used when too few stocks returned usable price data."""
    timestamp = result.as_of.astimezone(IST) if result.as_of is not None else None
    return AlertMessage(
        title="Nifty 500 Market Movers — data warning",
        sections=(
            AlertSection(
                "Warning",
                (
                    f"Only {result.scanned_count} of {expected_count} stocks "
                    "returned usable price data.",
                    "Skipping the movers list to avoid a misleading report.",
                ),
            ),
        ),
        footer=f"Scanned: {result.scanned_count} | Skipped: {result.skipped_count}",
        timestamp=timestamp,
    )


def _format_movers(movers: tuple[Mover, ...], empty_message: str) -> tuple[str, ...]:
    if not movers:
        return (empty_message,)

    return tuple(
        f"{mover.symbol}: Rs. {mover.last_price:,.2f} ({mover.pct_change:+.2f}%)"
        for mover in movers
    )
