"""Tests for application settings."""

from pathlib import Path

from pytest import MonkeyPatch

from market_radar.config import Settings


def test_settings_load_defaults(monkeypatch: MonkeyPatch) -> None:
    """Settings use documented defaults when no environment variables are supplied."""
    for variable in (
        "APP_ENV",
        "LOG_LEVEL",
        "TIMEZONE",
        "TOP_N",
        "UNIVERSE_CSV_PATH",
        "HOLIDAYS_CSV_PATH",
        "MIN_SUCCESS_RATIO",
        "DISCORD_WEBHOOK_URL",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.timezone == "Asia/Kolkata"
    assert settings.top_n == 10
    assert settings.universe_csv_path == Path("data/reference/nifty500.csv")
    assert settings.holidays_csv_path == Path("data/reference/nse_holidays_2026.csv")
    assert settings.min_success_ratio == 0.8
    assert settings.discord_webhook_url is None


def test_settings_environment_override(monkeypatch: MonkeyPatch) -> None:
    """Environment variables override the configured defaults."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TOP_N", "5")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/id/token")

    settings = Settings()

    assert settings.app_env == "production"
    assert settings.top_n == 5
    assert settings.discord_webhook_url is not None
    assert (
        settings.discord_webhook_url.get_secret_value()
        == "https://discord.com/api/webhooks/id/token"
    )


def test_empty_min_success_ratio_falls_back_to_default(monkeypatch: MonkeyPatch) -> None:
    """An empty MIN_SUCCESS_RATIO is ignored so the default applies instead of failing to parse."""
    monkeypatch.setenv("MIN_SUCCESS_RATIO", "")

    settings = Settings(_env_file=None)

    assert settings.min_success_ratio == 0.8


def test_empty_discord_webhook_is_treated_as_unset(monkeypatch: MonkeyPatch) -> None:
    """An empty DISCORD_WEBHOOK_URL is treated as not configured rather than a blank secret."""
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "")

    settings = Settings(_env_file=None)

    assert settings.discord_webhook_url is None
