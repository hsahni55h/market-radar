# Session: 2026-09-30 — Step 03: Scanner logic

**Branch:** `feature/step-03-scanner`
**Status at end of session:** Done

## Goal of this session
Implement pure logic that ranks daily gainers and losers from fetched quotes.

## What was done
- Added immutable `Mover` and `ScanResult` models plus deterministic percentage-change ranking.
- Added `top_n` configuration and tests for ordering, ties, flat prices, invalid quotes, and limits.
- Corrected the yfinance adapter to accept and return plain NSE symbols while converting `.NS` internally.
- Ran a full-universe manual check: 499 quotes scanned, with `BAGMANE` and `DUMMYHEG` skipped.

## Files created or changed
- `src/market_radar/scanner.py`
- `src/market_radar/config.py`
- `src/market_radar/providers/base.py`
- `src/market_radar/providers/yfinance_provider.py`
- `tests/test_scanner.py`
- `tests/test_config.py`
- `tests/providers/test_yfinance_provider.py`
- `docs/PLAN.md`
- `docs/DECISIONS.md`

## Dependencies added
- None

## Tests
- `make check`: pass (16 tests; 1 integration test deselected)

## Decisions made
- D-009 clarified: the yfinance provider accepts and returns plain NSE symbols.

## Problems and how they were solved
- Passing plain symbols to yfinance fetched some US tickers. The provider now adds `.NS` internally.

## Open issues / next steps
- Start Step 4: format scan results and deliver them through a Discord webhook.

## Suggested commit message
```
feat: add scanner ranking logic
```
