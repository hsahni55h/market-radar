"""Tests for the yfinance market-data provider."""

import logging
from collections.abc import Callable

import pandas as pd
import pytest

from market_radar.providers.yfinance_provider import YFinancePriceProvider, to_provider_symbol


def test_to_provider_symbol_adds_nse_suffix() -> None:
    """NSE symbols use the provider's .NS suffix."""
    assert to_provider_symbol("RELIANCE") == "RELIANCE.NS"


def test_get_quotes_converts_plain_symbols_for_yfinance(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The yfinance request receives NSE symbols with its required suffix."""
    caplog.set_level(logging.INFO)
    columns = pd.MultiIndex.from_tuples([("RELIANCE.NS", "Close"), ("MISSING.NS", "Close")])
    prices = pd.DataFrame(
        [[1_425.10, 100.0], [1_455.25, float("nan")]],
        columns=columns,
    )
    captured_tickers: list[str] = []
    download = _download_returning(prices, captured_tickers)
    monkeypatch.setattr(
        "market_radar.providers.yfinance_provider.yf.download",
        download,
    )

    YFinancePriceProvider().get_quotes(["RELIANCE", "MISSING"])

    assert captured_tickers == ["RELIANCE.NS", "MISSING.NS"]
    assert "Fetched price data for 2 symbols" in caplog.text


def test_get_quotes_returns_plain_symbols_in_quotes_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A batch preserves valid plain symbols when another symbol has invalid prices."""
    columns = pd.MultiIndex.from_tuples([("RELIANCE.NS", "Close"), ("MISSING.NS", "Close")])
    prices = pd.DataFrame(
        [[1_425.10, 100.0], [1_455.25, float("nan")]],
        columns=columns,
    )
    monkeypatch.setattr(
        "market_radar.providers.yfinance_provider.yf.download",
        _download_returning(prices),
    )

    batch = YFinancePriceProvider().get_quotes(["RELIANCE", "MISSING"])

    assert len(batch.quotes) == 1
    assert batch.quotes[0].symbol == "RELIANCE"
    assert batch.quotes[0].last_price == 1_455.25
    assert batch.quotes[0].previous_close == 1_425.10
    assert batch.quotes[0].as_of.tzinfo is not None
    assert batch.failed_symbols == ("MISSING",)


def test_get_quotes_returns_all_symbols_when_download_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A batch-wide provider error becomes per-symbol failures."""
    monkeypatch.setattr(
        "market_radar.providers.yfinance_provider.yf.download",
        _download_raising,
    )

    batch = YFinancePriceProvider().get_quotes(["RELIANCE", "TCS"])

    assert batch.quotes == ()
    assert batch.failed_symbols == ("RELIANCE", "TCS")


def test_get_quotes_does_not_download_empty_symbol_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty request returns immediately without calling yfinance."""
    monkeypatch.setattr(
        "market_radar.providers.yfinance_provider.yf.download",
        _download_raising,
    )

    batch = YFinancePriceProvider().get_quotes([])

    assert batch.quotes == ()
    assert batch.failed_symbols == ()


@pytest.mark.integration
def test_get_quotes_fetches_real_quote() -> None:
    """The provider retrieves a quote from yfinance when the network is available."""
    batch = YFinancePriceProvider().get_quotes(["RELIANCE"])

    assert len(batch.quotes) == 1
    assert batch.failed_symbols == ()


def _download_returning(
    prices: pd.DataFrame,
    captured_tickers: list[str] | None = None,
) -> Callable[..., pd.DataFrame]:
    def download(**kwargs: object) -> pd.DataFrame:
        tickers = kwargs["tickers"]
        if captured_tickers is not None:
            if not isinstance(tickers, list):
                raise TypeError("tickers must be a list of strings")
            string_tickers = [ticker for ticker in tickers if isinstance(ticker, str)]
            if len(string_tickers) != len(tickers):
                raise TypeError("tickers must be a list of strings")
            captured_tickers.extend(string_tickers)
        return prices

    return download


def _download_raising(**_: object) -> pd.DataFrame:
    raise RuntimeError("provider unavailable")
