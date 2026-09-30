"""yfinance implementation of the market-data provider interface."""

import logging
import math
from collections.abc import Sequence
from datetime import UTC, datetime
from time import perf_counter

import pandas as pd
import yfinance as yf  # type: ignore[import-untyped]  # yfinance does not publish type metadata.

from market_radar.providers.base import PriceProvider, Quote, QuoteBatch

logger = logging.getLogger(__name__)


def to_provider_symbol(symbol: str) -> str:
    """Convert an NSE symbol to the yfinance ticker format."""
    return f"{symbol}.NS"


class YFinancePriceProvider(PriceProvider):
    """Fetch end-of-day price data in one yfinance batch request."""

    def get_quotes(self, symbols: Sequence[str]) -> QuoteBatch:
        """Fetch prices for plain NSE symbols and return results using those symbols."""
        requested_symbols = tuple(symbols)
        if not requested_symbols:
            return QuoteBatch(quotes=(), failed_symbols=())

        provider_symbols = tuple(to_provider_symbol(symbol) for symbol in requested_symbols)

        started_at = perf_counter()
        try:
            prices = yf.download(
                tickers=list(provider_symbols),
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                multi_level_index=True,
            )
        except Exception:
            logger.exception("Price download failed for %d symbols", len(requested_symbols))
            return QuoteBatch(quotes=(), failed_symbols=requested_symbols)
        finally:
            elapsed_seconds = perf_counter() - started_at
            logger.info(
                "Fetched price data for %d symbols in %.2f seconds",
                len(requested_symbols),
                elapsed_seconds,
            )

        as_of = datetime.now(UTC)
        quotes: list[Quote] = []
        failed_symbols: list[str] = []
        for symbol in requested_symbols:
            provider_symbol = to_provider_symbol(symbol)
            quote = _quote_from_prices(prices, provider_symbol, symbol, as_of)
            if quote is None:
                logger.warning("Missing or invalid price data for %s", symbol)
                failed_symbols.append(symbol)
            else:
                quotes.append(quote)

        return QuoteBatch(quotes=tuple(quotes), failed_symbols=tuple(failed_symbols))


def _quote_from_prices(
    prices: pd.DataFrame,
    provider_symbol: str,
    symbol: str,
    as_of: datetime,
) -> Quote | None:
    try:
        closes = prices[provider_symbol]["Close"].dropna()
    except (KeyError, TypeError):
        return None

    if len(closes) < 2:
        return None

    try:
        previous_close = float(closes.iloc[-2])
        last_price = float(closes.iloc[-1])
    except (TypeError, ValueError):
        return None

    if not all(math.isfinite(value) and value > 0 for value in (last_price, previous_close)):
        return None

    return Quote(
        symbol=symbol,
        last_price=last_price,
        previous_close=previous_close,
        as_of=as_of,
    )
