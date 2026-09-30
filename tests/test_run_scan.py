"""Tests for the scan pipeline orchestration."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from market_radar.alerts.message import AlertMessage
from market_radar.config import Settings
from market_radar.providers.base import Quote, QuoteBatch
from market_radar.run_scan import run_scan

AS_OF = datetime(2026, 9, 30, 10, 15, tzinfo=UTC)

UNIVERSE_ROWS = (
    ("Alpha Ltd", "Finance", "ALPHA", "INE000A01001"),
    ("Beta Ltd", "Energy", "BETA", "INE000A01002"),
    ("Gamma Ltd", "Pharma", "GAMMA", "INE000A01003"),
)


class FakeProvider:
    """A price provider that returns a preset batch and records requested symbols."""

    def __init__(self, batch: QuoteBatch) -> None:
        self._batch = batch
        self.requested_symbols: tuple[str, ...] = ()

    def get_quotes(self, symbols: Sequence[str]) -> QuoteBatch:
        self.requested_symbols = tuple(symbols)
        return self._batch


class FakeNotifier:
    """A notifier that records delivered messages."""

    def __init__(self) -> None:
        self.messages: list[AlertMessage] = []

    def send(self, message: AlertMessage) -> None:
        self.messages.append(message)


class FailingNotifier:
    """A notifier that always fails delivery."""

    def send(self, message: AlertMessage) -> None:
        raise RuntimeError("delivery failed")


def _quote(symbol: str, last_price: float, previous_close: float) -> Quote:
    return Quote(
        symbol=symbol,
        last_price=last_price,
        previous_close=previous_close,
        as_of=AS_OF,
    )


def _write_universe(path: Path) -> None:
    lines = ["Company Name,Industry,Symbol,ISIN Code"]
    lines += [",".join(row) for row in UNIVERSE_ROWS]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _settings(universe_path: Path, *, min_success_ratio: float = 0.8) -> Settings:
    return Settings(
        _env_file=None,
        universe_csv_path=universe_path,
        min_success_ratio=min_success_ratio,
        top_n=10,
    )


def test_run_scan_delivers_movers_message(tmp_path: Path) -> None:
    """A healthy scan ranks movers and delivers the standard movers alert."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    batch = QuoteBatch(
        quotes=(
            _quote("ALPHA", 120, 100),
            _quote("BETA", 100, 100),
            _quote("GAMMA", 80, 100),
        ),
        failed_symbols=(),
    )
    provider = FakeProvider(batch)
    notifier = FakeNotifier()

    result = run_scan(provider, notifier, _settings(universe))

    assert provider.requested_symbols == ("ALPHA", "BETA", "GAMMA")
    assert [mover.symbol for mover in result.gainers] == ["ALPHA"]
    assert [mover.symbol for mover in result.losers] == ["GAMMA"]
    assert len(notifier.messages) == 1
    assert notifier.messages[0].title == "Nifty 500 Market Movers"


def test_run_scan_sends_warning_when_too_few_quotes(tmp_path: Path) -> None:
    """Below the success threshold, a data warning replaces the movers list."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    batch = QuoteBatch(
        quotes=(_quote("ALPHA", 120, 100),),
        failed_symbols=("BETA", "GAMMA"),
    )
    provider = FakeProvider(batch)
    notifier = FakeNotifier()

    run_scan(provider, notifier, _settings(universe, min_success_ratio=0.8))

    assert len(notifier.messages) == 1
    message = notifier.messages[0]
    assert message.title == "Nifty 500 Market Movers — data warning"
    assert message.sections[0].heading == "Warning"


def test_run_scan_propagates_notifier_failure(tmp_path: Path) -> None:
    """A delivery failure is not swallowed by the pipeline."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    batch = QuoteBatch(quotes=(_quote("ALPHA", 120, 100),), failed_symbols=())
    provider = FakeProvider(batch)

    with pytest.raises(RuntimeError, match="delivery failed"):
        run_scan(provider, FailingNotifier(), _settings(universe, min_success_ratio=0.0))


def test_run_scan_counts_failed_fetches_as_skipped(tmp_path: Path) -> None:
    """Symbols the provider failed to fetch are reported in the skipped count."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    batch = QuoteBatch(
        quotes=(_quote("ALPHA", 120, 100), _quote("BETA", 100, 100)),
        failed_symbols=("GAMMA",),
    )
    provider = FakeProvider(batch)
    notifier = FakeNotifier()

    result = run_scan(provider, notifier, _settings(universe, min_success_ratio=0.0))

    assert result.scanned_count == 2
    assert result.skipped_count == 1
    assert notifier.messages[0].footer == "Scanned: 2 | Skipped: 1"
