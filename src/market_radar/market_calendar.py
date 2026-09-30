"""Trading-day calendar for the NSE equity market.

Pure logic apart from reading the holiday CSV. `is_trading_day` takes the date to
check as an argument so callers own the clock and tests never depend on it.
"""

import csv
import logging
from collections.abc import Mapping
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

SATURDAY = 5
SUNDAY = 6


def load_holidays(path: Path) -> frozenset[date]:
    """Load NSE holiday dates from a CSV, or return an empty set if the file is missing."""
    try:
        with path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None or "date" not in reader.fieldnames:
                raise ValueError("Holiday CSV must have a 'date' column")
            return frozenset(
                _parse_date(row, row_number) for row_number, row in enumerate(reader, start=2)
            )
    except FileNotFoundError:
        logger.warning("Holiday file %s not found; treating all weekdays as trading days", path)
        return frozenset()


def is_trading_day(day: date, holidays: frozenset[date]) -> bool:
    """Return whether the NSE trades on the given day: a weekday that is not a holiday."""
    if day.weekday() in (SATURDAY, SUNDAY):
        return False
    return day not in holidays


def _parse_date(row: Mapping[str, str | None], row_number: int) -> date:
    value = (row.get("date") or "").strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        message = f"Invalid date {value!r} at row {row_number}"
        raise ValueError(message) from None
