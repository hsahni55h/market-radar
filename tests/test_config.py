"""Tests for application settings."""

from pytest import MonkeyPatch

from market_radar.config import Settings


def test_settings_load_defaults(monkeypatch: MonkeyPatch) -> None:
    """Settings use documented defaults when no environment variables are supplied."""
    for variable in (
        "APP_ENV",
        "LOG_LEVEL",
        "TIMEZONE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings()

    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.timezone == "Asia/Kolkata"
    assert settings.telegram_bot_token is None
    assert settings.telegram_chat_id is None


def test_settings_environment_override(monkeypatch: MonkeyPatch) -> None:
    """Environment variables override the configured defaults."""
    monkeypatch.setenv("APP_ENV", "production")

    settings = Settings()

    assert settings.app_env == "production"
