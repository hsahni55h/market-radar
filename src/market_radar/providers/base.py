"""Provider-neutral market-data models and interfaces."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Quote:
    """A latest price and previous close for one canonical market symbol."""

    symbol: str
    last_price: float
    previous_close: float
    as_of: datetime


@dataclass(frozen=True, slots=True)
class QuoteBatch:
    """The successfully fetched quotes and symbols that could not be quoted."""

    quotes: tuple[Quote, ...]
    failed_symbols: tuple[str, ...]


class PriceProvider(Protocol):
    """Fetch market prices without exposing a provider-specific API to callers."""

    def get_quotes(self, symbols: Sequence[str]) -> QuoteBatch:
        """Return quotes and failed symbols using the supplied canonical symbols."""
