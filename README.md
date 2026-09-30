# Market Radar

Market Radar is a personal Indian stock-market monitoring tool for three family users.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
make install
cp .env.example .env
```

## Commands

```sh
make lint       # Run linting and formatting checks
make format     # Apply lint and formatting fixes
make typecheck  # Run strict type checking
make test       # Run tests with coverage
make check      # Run all validation checks
make run        # Run a scan and post the alert to Discord
make dry-run    # Run a scan and print the alert to the console
```

## Automation

The scan runs automatically in GitHub Actions ([`.github/workflows/scan.yml`](.github/workflows/scan.yml)),
so no laptop is involved.

Schedule (Monday–Friday; the app itself skips NSE holidays):

| IST | UTC | Purpose |
| --- | --- | --- |
| 10:15–15:15, hourly | 04:45–09:45 (`45 4-9 * * 1-5`) | Trading-hours scans |
| 15:35 | 10:05 (`5 10 * * 1-5`) | Closing scan |

GitHub may start scheduled runs a few minutes late.

**Manual run:** in the repository's **Actions → Scheduled scan → Run workflow** button.
It offers a `dry_run` toggle (default on) that logs the alert instead of sending it; scheduled
runs always send for real.

**Required configuration** (repository settings, never in code):

- Secret `DISCORD_WEBHOOK_URL` — the family channel webhook.
- Variable `MIN_SUCCESS_RATIO` — minimum share of quotes that must succeed; if unset or empty,
  the app falls back to its default.
