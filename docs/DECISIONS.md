# Decisions

Record every decision that shapes the design, so future sessions don't undo it by accident.
Newest first. Format: ID, date, decision, reason, consequences.

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
