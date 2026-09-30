"""Orchestration for a single market scan run."""

import logging
from dataclasses import replace

from market_radar.alerts.base import Notifier
from market_radar.alerts.message import AlertMessage
from market_radar.config import Settings
from market_radar.formatter import format_low_data_warning, format_scan
from market_radar.providers.base import PriceProvider
from market_radar.scanner import ScanResult, rank_movers
from market_radar.universe import load_universe

logger = logging.getLogger(__name__)


def run_scan(provider: PriceProvider, notifier: Notifier, settings: Settings) -> ScanResult:
    """Run the scan pipeline end to end and deliver the resulting alert.

    Providers and notifiers are injected so the pipeline can be tested with fakes.
    """
    instruments = load_universe(settings.universe_csv_path)
    symbols = [instrument.symbol for instrument in instruments]

    batch = provider.get_quotes(symbols)
    ranked = rank_movers(batch.quotes, top_n=settings.top_n)
    # Symbols the provider could not fetch are skipped alongside quotes rejected as invalid.
    result = replace(ranked, skipped_count=ranked.skipped_count + len(batch.failed_symbols))

    expected_count = len(symbols)
    success_ratio = result.scanned_count / expected_count if expected_count else 0.0

    message: AlertMessage
    if success_ratio < settings.min_success_ratio:
        logger.warning(
            "Only %d of %d stocks returned usable data (%.0f%%); sending data warning",
            result.scanned_count,
            expected_count,
            success_ratio * 100,
        )
        message = format_low_data_warning(result, expected_count)
    else:
        message = format_scan(result)

    notifier.send(message)

    logger.info(
        "Scan complete: %d gainers, %d losers, %d scanned, %d skipped, %d failed to fetch",
        len(result.gainers),
        len(result.losers),
        result.scanned_count,
        result.skipped_count,
        len(batch.failed_symbols),
    )
    return result
