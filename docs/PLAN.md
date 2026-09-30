# Market Radar — Development Plan

> **This file is the source of truth for what gets built and in what order.**
> Work on one step at a time, in order. Do not start a step until the previous one is marked done.
> Update the status table and checkboxes at the end of every session.

## Current status

| Field | Value |
| --- | --- |
| Current version | v1 — Market Scanner + Discord alerts |
| Current step | Step 4 — Message formatting and Discord notifier |
| Last session log | `2026-09-30-step-03-scanner-logic.md` |
| Last updated | 2026-09-30 |

## v1 goal

Prove the core idea is feasible: every trading hour, find the top 10 gainers and top 10 losers
in the Nifty 500 and post them to a private family Discord channel, running automatically in the
cloud with no laptop involved.

**v1 is done when:** it runs unattended for 5 consecutive trading days with no missed runs,
lists that match NSE spot checks, and no crashes (Step 9).

## Definition of done (applies to every step)

- [ ] Code written with full type hints, following `.github/copilot-instructions.md`
- [ ] Unit tests for all logic; no network calls in unit tests
- [ ] `make check` passes (ruff, mypy strict, pytest)
- [ ] Acceptance criteria of the step verified by the user
- [ ] `docs/PLAN.md` status and checkboxes updated
- [ ] Session log written in `docs/sessions/`
- [ ] Any new decision recorded in `docs/DECISIONS.md`
- [ ] PR merged into `main` with CI green

---

## Step 0 — Project foundation ✅ DONE

uv project with src layout, ruff, mypy (strict), pytest, pre-commit, Makefile, CI workflow,
`Settings` via pydantic-settings, logging setup.

---

## Step 1 — Stock universe ✅ DONE

**Branch:** `feature/step-01-universe`
**Goal:** a reliable list of the Nifty 500 stocks the scanner will cover.

Scope:
- [x] Save the official Nifty 500 constituents CSV (from NSE Indices) to `data/reference/nifty500.csv` and commit it
- [x] `src/market_radar/universe.py` with a frozen dataclass `Instrument` (symbol, company_name, industry, isin)
- [x] `load_universe(path) -> list[Instrument]`, validating required columns and rejecting duplicates
- [x] Helper to convert an NSE symbol to the provider format (`RELIANCE` → `RELIANCE.NS`) — keep provider-specific formatting out of the domain model if possible
- [x] Tests: correct count, no duplicates, malformed file raises a clear error

Acceptance: loading the file returns ~500 instruments; tests pass.
Out of scope: fetching the list automatically from the internet.

---

## Step 2 — Price provider (yfinance) ✅ DONE

**Branch:** `feature/step-02-price-provider`
**Goal:** fetch current price and previous close for all stocks in one run.

Scope:
- [x] Add `yfinance` dependency via `uv add`
- [x] `src/market_radar/providers/base.py`: frozen dataclass `Quote` (symbol, last_price, previous_close, as_of) and a `PriceProvider` Protocol with `get_quotes(symbols) -> QuoteBatch` (quotes + list of failed symbols)
- [x] `src/market_radar/providers/yfinance_provider.py` implementing it with batched downloads
- [x] Symbols with missing/invalid data are logged and returned as failed, never crash the run
- [x] Timing is logged for each fetch
- [x] Unit tests with a mocked yfinance response; one integration test marked `@pytest.mark.integration` (skipped by default)

Acceptance:
- [x] A manual run returns quotes for ≥ 95% of the universe in under 60 seconds.
- [x] User spot-checked 5 prices against the NSE website.
Out of scope: broker APIs, caching, storage.

---

## Step 3 — Scanner logic ✅ DONE

**Branch:** `feature/step-03-scanner`
**Goal:** rank the day's biggest movers. Pure logic, no I/O.

Scope:
- [x] `src/market_radar/scanner.py`: `Mover` (symbol, last_price, previous_close, pct_change) and `ScanResult` (gainers, losers, scanned_count, skipped_count, as_of)
- [x] `rank_movers(quotes, top_n=10) -> ScanResult` — % change vs previous close
- [x] Excludes quotes with missing or zero previous close; deterministic ordering on ties (by symbol)
- [x] `top_n` comes from `Settings` (default 10)
- [x] Tests: ordering, ties, fewer than 10 stocks, all stocks flat, invalid quotes excluded

Acceptance: tests pass; a manual run prints both top-10 lists in the terminal.

---

## Step 4 — Message formatting and Discord notifier

**Branch:** `feature/step-04-discord`
**Goal:** turn a `ScanResult` into a readable message and post it to the family Discord channel.

Scope:
- [ ] User creates the family Discord server, a private `#market-scanner` channel and a webhook for it, and puts the webhook URL in `.env`
- [ ] Replace the Telegram fields in `Settings` and `.env.example` with `discord_webhook_url: SecretStr | None`
- [ ] `src/market_radar/alerts/message.py`: a channel-neutral frozen dataclass `AlertMessage` (title, sections with headings and lines, footer, timestamp) — so the same message can later go to email or other channels
- [ ] `src/market_radar/formatter.py`: pure function `format_scan(result) -> AlertMessage` (time in IST, gainers, losers, scanned/skipped counts)
- [ ] `src/market_radar/alerts/base.py`: `Notifier` Protocol with `send(message: AlertMessage) -> None`
- [ ] `src/market_radar/alerts/discord.py`: renders `AlertMessage` as a Discord embed (gainers and losers as two fields) and posts it via `httpx` (add via `uv add`); timeout, simple retry, respects HTTP 429 rate-limit responses; stays within Discord's embed size limits
- [ ] `ConsoleNotifier` that logs the message instead of sending it (used for dry runs)
- [ ] The webhook URL is a secret: never logged, never printed in errors
- [ ] Tests: formatter tests; Discord payload-building tests; notifier tested with a mocked HTTP client

Acceptance: a test message appears in `#market-scanner` and looks right on a phone, and all three
family members receive a push notification for it.

---

## Step 5 — Scan runner and CLI

**Branch:** `feature/step-05-runner`
**Goal:** one command runs the whole pipeline end to end.

Scope:
- [ ] `src/market_radar/run_scan.py`: `run_scan(provider, notifier, settings) -> ScanResult` — dependencies are passed in, not created inside, so it is testable
- [ ] CLI via `argparse` in `__main__.py`: `uv run python -m market_radar scan [--dry-run]`
- [ ] Clear exit codes (0 success, non-zero failure) and a one-line run summary in the log
- [ ] If fewer than a configurable share of quotes succeed, send a warning instead of a misleading list
- [ ] Tests: full pipeline with fake provider and fake notifier

Acceptance: `scan --dry-run` prints the message; `scan` posts it to Discord.

---

## Step 6 — Market calendar

**Branch:** `feature/step-06-market-calendar`
**Goal:** never run or alert on weekends and NSE holidays.

Scope:
- [ ] `data/reference/nse_holidays_2026.csv` (and 2027 when published)
- [ ] `src/market_radar/market_calendar.py`: `is_trading_day(date) -> bool`, IST-aware
- [ ] If the holiday file for the current year is missing, log a warning and treat weekdays as trading days
- [ ] `run_scan` exits early with a log line on non-trading days
- [ ] Tests: weekend, holiday, normal day, missing year file

Acceptance: running on a Saturday or holiday logs "market closed" and sends nothing.

---

## Step 7 — Scheduled cloud runs (GitHub Actions)

**Branch:** `feature/step-07-scheduled-scan`
**Goal:** the scan runs hourly in the cloud with no laptop.

Scope:
- [ ] `.github/workflows/scan.yml` with `schedule` cron (in UTC) for 10:15, 11:15, 12:15, 13:15, 14:15, 15:15 and 15:35 IST, Monday–Friday, plus `workflow_dispatch` for manual runs
- [ ] Uses `astral-sh/setup-uv`, `uv sync --frozen`, then runs the CLI
- [ ] `DISCORD_WEBHOOK_URL` stored as a repository secret, never in code
- [ ] Job timeout and a `concurrency` group so two runs never overlap
- [ ] Workflow failure is visible (GitHub notifies the repo owner by email)

Acceptance: a manual `workflow_dispatch` run delivers a message; the next scheduled run fires on
its own. Note: GitHub may start scheduled runs several minutes late — record how late in Step 9.

---

## Step 8 — Email fallback (optional)

**Branch:** `feature/step-08-email`
**Goal:** a second delivery channel if Discord fails.

Scope:
- [ ] `src/market_radar/alerts/email.py` using `smtplib` (Gmail app password in secrets)
- [ ] `FallbackNotifier` that tries Discord, then email
- [ ] Tests with mocked SMTP

Acceptance: breaking the Discord webhook URL on purpose results in an email.

---

## Step 9 — Feasibility week

**Branch:** none (observation). Findings go in `docs/sessions/`.
**Goal:** decide whether v1 works well enough to build on.

Track for 5 trading days:

| Day | Runs expected | Runs delivered | Max delay (min) | Spot check OK | Skipped stocks | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 7 | | | | | |
| 2 | 7 | | | | | |
| 3 | 7 | | | | | |
| 4 | 7 | | | | | |
| 5 | 7 | | | | | |

Questions to answer: Is yfinance reliable enough, or do we move to a broker API? Is hourly the
right frequency? Is the message useful to all three users?

---

## Roadmap beyond v1 (not to be started yet)

| Version | Theme | Main pieces |
| --- | --- | --- |
| v2 | Data and portfolios | PostgreSQL, transaction ledger per user, holdings and P/L, watchlist price triggers, alert engine with events, possibly broker API |
| v3 | Dashboard | FastAPI backend + React (TypeScript, Vite) in `frontend/`; login-protected; private hosting (GitHub Pages is public, so not suitable) — hosting choice open |
| v4 | News intelligence | News and exchange-filing collectors, linking news to stocks |
| v5 | AI summaries and analysis | Daily recap, why-did-it-move explanations, weekly/monthly reviews |
