"""Tests for stock-universe loading."""

from pathlib import Path

import pytest

from market_radar.universe import Instrument, load_universe

REFERENCE_CSV = Path(__file__).parents[1] / "data" / "reference" / "nifty500.csv"


def test_load_universe_reads_reference_data() -> None:
    """The committed reference file loads into unique Nifty 500 instruments."""
    instruments = load_universe(REFERENCE_CSV)

    # The count shifts whenever NSE rebalances the index, so assert a sensible range.
    assert 480 <= len(instruments) <= 520
    assert len({instrument.symbol for instrument in instruments}) == len(instruments)
    assert instruments[0] == Instrument(
        symbol="360ONE",
        company_name="360 ONE WAM Ltd.",
        industry="Financial Services",
        isin="INE466L01038",
    )


def test_load_universe_rejects_missing_required_column(tmp_path: Path) -> None:
    """A malformed CSV identifies its missing required column."""
    csv_path = tmp_path / "universe.csv"
    csv_path.write_text("Company Name,Industry,Symbol\nExample,Services,EXAMPLE\n")

    with pytest.raises(ValueError, match="Missing required columns: ISIN Code"):
        load_universe(csv_path)


def test_load_universe_rejects_duplicate_symbols(tmp_path: Path) -> None:
    """Duplicate symbols are rejected because symbols identify instruments."""
    csv_path = tmp_path / "universe.csv"
    csv_path.write_text(
        "Company Name,Industry,Symbol,ISIN Code\n"
        "Example One,Services,EXAMPLE,INE000000001\n"
        "Example Two,Services,EXAMPLE,INE000000002\n"
    )

    with pytest.raises(ValueError, match="Duplicate symbol 'EXAMPLE' at row 3"):
        load_universe(csv_path)


def test_load_universe_rejects_missing_required_value(tmp_path: Path) -> None:
    """A malformed row identifies its missing required value."""
    csv_path = tmp_path / "universe.csv"
    csv_path.write_text("Company Name,Industry,Symbol,ISIN Code\nExample,Services,,INE000000001\n")

    with pytest.raises(ValueError, match="Missing value for 'Symbol' at row 2"):
        load_universe(csv_path)
