"""Tests for the NSE trading-day calendar."""

from datetime import date
from pathlib import Path

import pytest

from market_radar.market_calendar import is_trading_day, load_holidays

REFERENCE_CSV = Path(__file__).parents[1] / "data" / "reference" / "nse_holidays_2026.csv"


def test_load_holidays_reads_reference_file() -> None:
    """The committed 2026 holiday file loads into the expected dates."""
    holidays = load_holidays(REFERENCE_CSV)

    assert len(holidays) == 16
    assert date(2026, 1, 26) in holidays
    assert date(2026, 12, 25) in holidays


def test_load_holidays_missing_file_returns_empty(tmp_path: Path) -> None:
    """A missing holiday file yields an empty set without raising."""
    holidays = load_holidays(tmp_path / "does-not-exist.csv")

    assert holidays == frozenset()


def test_load_holidays_rejects_missing_date_column(tmp_path: Path) -> None:
    """A CSV without a 'date' column is a clear error."""
    csv_path = tmp_path / "holidays.csv"
    csv_path.write_text("day,description\n2026-01-26,Republic Day\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must have a 'date' column"):
        load_holidays(csv_path)


def test_is_trading_day_normal_weekday() -> None:
    """A weekday that is not a holiday is a trading day."""
    # 2026-09-30 is a Wednesday.
    assert is_trading_day(date(2026, 9, 30), frozenset()) is True


def test_is_trading_day_weekend_without_csv_entry() -> None:
    """Weekends are non-trading days even with no holiday entries."""
    # 2026-10-03 is a Saturday, 2026-10-04 a Sunday.
    assert is_trading_day(date(2026, 10, 3), frozenset()) is False
    assert is_trading_day(date(2026, 10, 4), frozenset()) is False


def test_is_trading_day_listed_holiday() -> None:
    """A weekday listed as a holiday is a non-trading day."""
    holidays = frozenset({date(2026, 1, 26)})

    # 2026-01-26 (Republic Day) is a Monday.
    assert is_trading_day(date(2026, 1, 26), holidays) is False
