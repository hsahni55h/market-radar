# Decisions

Record every decision that shapes the design, so future sessions don't undo it by accident.
Newest first. Format: ID, date, decision, reason, consequences.

---

### D-011 · 2026-09-30 · Trading-day calendar is IST-aware, pure, and caller-driven
**Decision:** `market_calendar.is_trading_day(day, holidays)` is pure and takes the date as an argument; `load_holidays(path)` is the only I/O. `run_scan` computes "today" from the configured timezone (`Asia/Kolkata`), not the laptop's local date, and exits early (sending nothing, exit code 0) on weekends and dates listed in `data/reference/nse_holidays_2026.csv`. A missing holiday file logs a warning and treats weekdays as trading days rather than crashing. Weekends are non-trading regardless of the CSV. A `--force` flag on `scan` skips the check so the app can be tested on non-trading days. Market-hours logic is deliberately out of scope; the Step 7 schedule owns the hours.
**Reason:** the user is in a different timezone from the market, so the date must be India's; tests must never depend on the real clock; and a missing file should degrade gracefully.
**Consequences:** callers own the clock (easy, deterministic tests). The holiday file is year-specific (`nse_holidays_2026.csv`); refreshing each year (add 2027 when published) is required, and the default `holidays_csv_path` must be updated or overridden accordingly.

---

### D-010 · 2026-09-30 · Removed the DUMMYHEG and BAGMANE rows from the Nifty 500 reference file
**Decision:** removed `DUMMYHEG` (Dummy HEG Ltd., ISIN `DUM545A01024`) because it is a placeholder row, not a real listed company, and returns no data on Yahoo. Also removed `BAGMANE` (Bagmane Prime Office REIT): it trades on BSE (`BAGMANE.BO` on Yahoo) but not on NSE via Yahoo, and our provider only queries `.NS`, so it failed every scan. It can be restored if a BSE fallback is added or the data source changes.
**Reason:** the universe should contain only instruments that return usable data through the current provider; both rows were guaranteed to fail every scan.
**Consequences:** the file is otherwise the official NSE list — note these removals (and re-check BAGMANE's NSE availability) when refreshing it.

---

### D-009 · 2026-09-30 · NSE ticker formatting belongs to the yfinance provider
**Decision:** `YFinancePriceProvider` accepts and returns plain NSE symbols, converting to the `.NS` yfinance format internally; the universe module remains provider-neutral.
**Reason:** the Nifty 500 universe is provider-neutral; ticker suffixes are a yfinance implementation detail.
**Consequences:** callers never use provider-formatted symbols, and a replacement provider owns its own symbol conversion without changing universe loading.

---

### D-008 · 2026-09-29 · Copilot never commits, pushes or merges
**Reason:** the user reviews every change before it reaches Git.
**Consequences:** Copilot ends each session by suggesting a commit message.

### D-007 · 2026-09-29 · React frontend arrives in v3, in `frontend/`
**Decision:** React + TypeScript + Vite, in a `frontend/` folder next to the Python code at the repo root; backed by FastAPI.
**Reason:** v1 has no UI; building one now would double the work before the idea is proven. Deciding the location now avoids restructuring later.
**Consequences:** hosting must be private — GitHub Pages is public and therefore unsuitable. Hosting is an open question for v3.

### D-006 · 2026-09-29 · GitHub Actions is the v1 scheduler
**Decision:** a cron workflow runs the scan hourly in the cloud. No local scheduler (APScheduler) in v1.
**Reason:** no server or laptop needed; free for this volume; the app stays a simple run-once CLI.
**Consequences:** runs are stateless (no database in v1); scheduled runs may start a few minutes late.

### D-005 · 2026-09-29 · Discord is the primary alert channel (replaces Telegram)
**Decision:** alerts are posted to a private channel on a family Discord server via a webhook.
**Reason:** free, rich formatting (embeds), push notifications on phones, and room to grow — separate channels per topic or per person later. A webhook needs no bot account. The family has agreed to use Discord.
**Consequences:** the webhook URL is a secret (anyone holding it can post). Messages are built as a channel-neutral `AlertMessage`, so email or other channels can be added without changing the formatter. Telegram, WhatsApp and SMS were considered and set aside.

### D-004 · 2026-09-29 · Movement = % change vs previous close
**Reason:** simple, standard, matches exchange "gainers/losers" lists. Unusual-move detection (vs normal volatility) comes in a later version.

### D-003 · 2026-09-29 · Universe = Nifty 500
**Reason:** covers most of the market's value and avoids illiquid stocks with misleading % moves.

### D-002 · 2026-09-29 · yfinance for v1 data, behind a `PriceProvider` interface
**Reason:** free, no account or key, enough to test feasibility.
**Consequences:** unofficial and may break or lag; the interface lets us switch to a broker API by changing one file.

### D-001 · 2026-09-29 · Tooling: uv, src layout, ruff, mypy strict, pytest, pre-commit
**Reason:** modern, fast, consistent quality from day one.
