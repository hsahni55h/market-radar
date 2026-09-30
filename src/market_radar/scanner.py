"""Pure logic for ranking the market's largest daily price movements."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from market_radar.providers.base import Quote


@dataclass(frozen=True, slots=True)
class Mover:
    """A quote with its percentage change from the previous close."""

    symbol: str
    last_price: float
    previous_close: float
    pct_change: float


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Ranked gainers and losers from one market scan."""

    gainers: tuple[Mover, ...]
    losers: tuple[Mover, ...]
    scanned_count: int
    skipped_count: int
    as_of: datetime | None


def rank_movers(quotes: Sequence[Quote], top_n: int = 10) -> ScanResult:
    """Return the largest gainers and losers, excluding invalid price quotes."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    valid_quotes = tuple(
        quote for quote in quotes if quote.last_price > 0 and quote.previous_close > 0
    )
    movers = tuple(
        Mover(
            symbol=quote.symbol,
            last_price=quote.last_price,
            previous_close=quote.previous_close,
            pct_change=(quote.last_price - quote.previous_close) / quote.previous_close * 100,
        )
        for quote in valid_quotes
    )

    gainers = tuple(
        sorted(
            (mover for mover in movers if mover.pct_change > 0),
            key=lambda mover: (-mover.pct_change, mover.symbol),
        )[:top_n]
    )
    losers = tuple(
        sorted(
            (mover for mover in movers if mover.pct_change < 0),
            key=lambda mover: (mover.pct_change, mover.symbol),
        )[:top_n]
    )

    return ScanResult(
        gainers=gainers,
        losers=losers,
        scanned_count=len(valid_quotes),
        skipped_count=len(quotes) - len(valid_quotes),
        as_of=max((quote.as_of for quote in valid_quotes), default=None),
    )
