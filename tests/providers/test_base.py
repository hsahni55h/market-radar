"""Tests for provider-neutral market-data models."""

from datetime import UTC, datetime

from market_radar.providers.base import Quote, QuoteBatch


def test_quote_batch_represents_partial_provider_failure() -> None:
    """A batch retains successful quotes when another symbol fails."""
    quote = Quote(
        symbol="RELIANCE.NS",
        last_price=1_455.25,
        previous_close=1_425.10,
        as_of=datetime(2026, 9, 30, 10, 15, tzinfo=UTC),
    )

    batch = QuoteBatch(quotes=(quote,), failed_symbols=("MISSING.NS",))

    assert batch.quotes == (quote,)
    assert batch.failed_symbols == ("MISSING.NS",)
