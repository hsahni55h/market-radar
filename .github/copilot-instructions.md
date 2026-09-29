# Market Radar Development Conventions

- Use `uv` exclusively for Python and dependency management. Do not use `pip`, `venv`, Poetry, or `requirements.txt`.
- Keep the `src/` layout and the single `market_radar` package.
- Use full type hints and keep the code passing strict mypy checks.
- Use the `logging` module for runtime output; do not use `print`.
- Read configuration through `Settings`; environment variables and `.env` files are the only configuration sources.
- Never place secrets in source code or commit `.env` files.
- Add tests for all logic.
- Apply YAGNI: create small, focused modules only when a current feature needs them.
- Use conventional commit messages.
