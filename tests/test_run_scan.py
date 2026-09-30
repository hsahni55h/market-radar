"""Tests for the scan pipeline orchestration."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from pytest import MonkeyPatch

from market_radar.alerts.message import AlertMessage
from market_radar.config import Settings
from market_radar.providers.base import Quote, QuoteBatch
from market_radar.run_scan import run_scan

AS_OF = datetime(2026, 9, 30, 10, 15, tzinfo=UTC)
# 2026-09-30 is a Wednesday and not an NSE holiday.
TRADING_DAY = date(2026, 9, 30)

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

    result = run_scan(provider, notifier, _settings(universe), today=TRADING_DAY)

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

    run_scan(provider, notifier, _settings(universe, min_success_ratio=0.8), today=TRADING_DAY)

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
        run_scan(
            provider,
            FailingNotifier(),
            _settings(universe, min_success_ratio=0.0),
            today=TRADING_DAY,
        )


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

    result = run_scan(
        provider, notifier, _settings(universe, min_success_ratio=0.0), today=TRADING_DAY
    )

    assert result.scanned_count == 2
    assert result.skipped_count == 1
    assert notifier.messages[0].footer == "Scanned: 2 | Skipped: 1"


def test_run_scan_skips_on_weekend(tmp_path: Path) -> None:
    """On a weekend the pipeline sends nothing and returns an empty result."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    provider = FakeProvider(QuoteBatch(quotes=(_quote("ALPHA", 120, 100),), failed_symbols=()))
    notifier = FakeNotifier()

    # 2026-10-03 is a Saturday.
    result = run_scan(provider, notifier, _settings(universe), today=date(2026, 10, 3))

    assert notifier.messages == []
    assert provider.requested_symbols == ()
    assert result.scanned_count == 0


def test_run_scan_skips_on_listed_holiday(tmp_path: Path) -> None:
    """On a listed NSE holiday the pipeline sends nothing."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    provider = FakeProvider(QuoteBatch(quotes=(_quote("ALPHA", 120, 100),), failed_symbols=()))
    notifier = FakeNotifier()

    # 2026-01-26 (Republic Day) is a Monday in the committed holiday file.
    result = run_scan(provider, notifier, _settings(universe), today=date(2026, 1, 26))

    assert notifier.messages == []
    assert result.scanned_count == 0


def test_run_scan_force_runs_on_non_trading_day(tmp_path: Path) -> None:
    """The force flag bypasses the trading-day check so the scan still sends."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    provider = FakeProvider(QuoteBatch(quotes=(_quote("ALPHA", 120, 100),), failed_symbols=()))
    notifier = FakeNotifier()

    # A Saturday, but forced.
    run_scan(
        provider,
        notifier,
        _settings(universe, min_success_ratio=0.0),
        today=date(2026, 10, 3),
        force=True,
    )

    assert len(notifier.messages) == 1


def test_run_scan_uses_india_date_not_laptop_date(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The trading-day check uses the Asia/Kolkata date, not the laptop's local date."""
    universe = tmp_path / "universe.csv"
    _write_universe(universe)
    provider = FakeProvider(QuoteBatch(quotes=(_quote("ALPHA", 120, 100),), failed_symbols=()))
    notifier = FakeNotifier()

    instant = datetime(2026, 1, 26, 20, 0, tzinfo=UTC)

    class _FixedClock:
        @staticmethod
        def now(tz: tzinfo | None = None) -> datetime:
            return instant.astimezone(tz)

    monkeypatch.setattr("market_radar.run_scan.datetime", _FixedClock)

    # India and Sweden fall on different dates at this instant.
    assert instant.astimezone(ZoneInfo("Asia/Kolkata")).date() == date(2026, 1, 27)
    assert instant.astimezone(ZoneInfo("Europe/Stockholm")).date() == date(2026, 1, 26)

    # India's 2026-01-27 is a trading Tuesday; Sweden's 2026-01-26 is Republic Day.
    run_scan(provider, notifier, _settings(universe, min_success_ratio=0.0))

    assert len(notifier.messages) == 1
