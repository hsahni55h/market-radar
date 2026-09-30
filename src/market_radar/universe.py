"""Loading and normalizing the stock universe."""

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS = frozenset({"Company Name", "Industry", "Symbol", "ISIN Code"})


@dataclass(frozen=True, slots=True)
class Instrument:
    """A stock instrument in the monitored universe."""

    symbol: str
    company_name: str
    industry: str
    isin: str


def load_universe(path: Path) -> list[Instrument]:
    """Load instruments from a Nifty 500 CSV, rejecting invalid rows and duplicate symbols."""
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing_columns:
            missing_columns_text = ", ".join(sorted(missing_columns))
            message = f"Missing required columns: {missing_columns_text}"
            raise ValueError(message)

        instruments: list[Instrument] = []
        seen_symbols: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            instrument = Instrument(
                symbol=_required_value(row, "Symbol", row_number),
                company_name=_required_value(row, "Company Name", row_number),
                industry=_required_value(row, "Industry", row_number),
                isin=_required_value(row, "ISIN Code", row_number),
            )
            if instrument.symbol in seen_symbols:
                message = f"Duplicate symbol {instrument.symbol!r} at row {row_number}"
                raise ValueError(message)
            seen_symbols.add(instrument.symbol)
            instruments.append(instrument)

    return instruments


def to_provider_symbol(symbol: str) -> str:
    """Convert an NSE symbol to the provider's NSE ticker format."""
    return f"{symbol}.NS"


def _required_value(row: Mapping[str, str | list[str] | None], column: str, row_number: int) -> str:
    value = row.get(column)
    if not isinstance(value, str) or not value.strip():
        message = f"Missing value for {column!r} at row {row_number}"
        raise ValueError(message)
    return value.strip()
