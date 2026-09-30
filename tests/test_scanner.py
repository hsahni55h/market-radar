"""Tests for pure market-mover ranking."""

from datetime import UTC, datetime

import pytest

from market_radar.providers.base import Quote
from market_radar.scanner import rank_movers

AS_OF = datetime(2026, 9, 30, 10, 15, tzinfo=UTC)


def quote(symbol: str, last_price: float, previous_close: float) -> Quote:
    """Create a quote with a stable timestamp for ranking tests."""
    return Quote(
        symbol=symbol,
        last_price=last_price,
        previous_close=previous_close,
        as_of=AS_OF,
    )


def test_rank_movers_orders_gainers_and_losers() -> None:
    """Largest percentage moves appear first in their respective lists."""
    result = rank_movers(
        (
            quote("SMALL_GAIN", 105, 100),
            quote("LARGE_GAIN", 120, 100),
            quote("SMALL_LOSS", 95, 100),
            quote("LARGE_LOSS", 80, 100),
        )
    )

    assert [mover.symbol for mover in result.gainers] == ["LARGE_GAIN", "SMALL_GAIN"]
    assert [mover.symbol for mover in result.losers] == ["LARGE_LOSS", "SMALL_LOSS"]
    assert result.scanned_count == 4
    assert result.skipped_count == 0
    assert result.as_of == AS_OF


def test_rank_movers_sorts_ties_by_symbol_and_limits_results() -> None:
    """Equal movements are deterministic and each list respects top_n."""
    result = rank_movers(
        (
            quote("ZETA", 110, 100),
            quote("ALPHA", 110, 100),
            quote("BETA", 90, 100),
            quote("GAMMA", 90, 100),
        ),
        top_n=1,
    )

    assert [mover.symbol for mover in result.gainers] == ["ALPHA"]
    assert [mover.symbol for mover in result.losers] == ["BETA"]


def test_rank_movers_handles_flat_and_invalid_quotes() -> None:
    """Flat prices are counted while unusable prices are excluded."""
    result = rank_movers(
        (
            quote("FLAT", 100, 100),
            quote("NO_CLOSE", 100, 0),
            quote("NO_PRICE", 0, 100),
        )
    )

    assert result.gainers == ()
    assert result.losers == ()
    assert result.scanned_count == 1
    assert result.skipped_count == 2


def test_rank_movers_rejects_non_positive_top_n() -> None:
    """A ranking size must select at least one mover."""
    with pytest.raises(ValueError, match="top_n must be at least 1"):
        rank_movers((), top_n=0)
