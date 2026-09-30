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
