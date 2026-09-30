"""Tests for application settings."""

from pytest import MonkeyPatch

from market_radar.config import Settings


def test_settings_load_defaults(monkeypatch: MonkeyPatch) -> None:
    """Settings use documented defaults when no environment variables are supplied."""
    for variable in (
        "APP_ENV",
        "LOG_LEVEL",
        "TIMEZONE",
        "TOP_N",
        "DISCORD_WEBHOOK_URL",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.timezone == "Asia/Kolkata"
    assert settings.top_n == 10
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
