"""Tests for the command-line entry point."""

import pytest
from pytest import MonkeyPatch

import market_radar.__main__ as cli
from market_radar.alerts.base import Notifier
from market_radar.alerts.console import ConsoleNotifier
from market_radar.alerts.discord import DiscordNotificationError, DiscordNotifier
from market_radar.config import Settings
from market_radar.providers.base import PriceProvider
from market_radar.scanner import ScanResult


def _settings(webhook: str | None = None) -> Settings:
    return Settings(_env_file=None, discord_webhook_url=webhook)


def _empty_result() -> ScanResult:
    return ScanResult(gainers=(), losers=(), scanned_count=0, skipped_count=0, as_of=None)


def test_build_notifier_uses_console_for_dry_run() -> None:
    """A dry run always delivers through the console notifier."""
    notifier = cli._build_notifier(_settings(), dry_run=True)
    assert isinstance(notifier, ConsoleNotifier)


def test_build_notifier_uses_discord_when_configured() -> None:
    """A real run with a webhook builds the Discord notifier."""
    notifier = cli._build_notifier(
        _settings("https://discord.com/api/webhooks/id/token"), dry_run=False
    )
    assert isinstance(notifier, DiscordNotifier)


def test_build_notifier_requires_webhook_for_real_run() -> None:
    """A real run without a webhook is a configuration error."""
    with pytest.raises(cli.ConfigurationError, match="DISCORD_WEBHOOK_URL"):
        cli._build_notifier(_settings(), dry_run=False)


def test_run_scan_command_returns_config_error_without_webhook() -> None:
    """A missing webhook on a real run maps to the config-error exit code."""
    exit_code = cli._run_scan_command(_settings(), dry_run=False)
    assert exit_code == cli.EXIT_CONFIG_ERROR


def test_empty_webhook_exits_config_error_without_sending(monkeypatch: MonkeyPatch) -> None:
    """An empty DISCORD_WEBHOOK_URL is treated as unset: exit code 2 and no send attempted."""
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "")
    settings = Settings(_env_file=None)

    def fail_if_called(
        provider: PriceProvider, notifier: Notifier, settings: Settings, *, force: bool = False
    ) -> ScanResult:
        raise AssertionError("run_scan must not be called when the webhook is unset")

    monkeypatch.setattr(cli, "run_scan", fail_if_called)

    exit_code = cli._run_scan_command(settings, dry_run=False)

    assert settings.discord_webhook_url is None
    assert exit_code == cli.EXIT_CONFIG_ERROR


def test_run_scan_command_maps_delivery_failure_to_failure_code(monkeypatch: MonkeyPatch) -> None:
    """A Discord delivery failure exits non-zero without leaking the webhook."""

    def fake_run_scan(
        provider: PriceProvider, notifier: Notifier, settings: Settings, *, force: bool = False
    ) -> ScanResult:
        raise DiscordNotificationError("Discord alert delivery failed")

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    exit_code = cli._run_scan_command(_settings(), dry_run=True)

    assert exit_code == cli.EXIT_FAILURE


def test_run_scan_command_returns_success(monkeypatch: MonkeyPatch) -> None:
    """A completed scan returns the success exit code."""

    def fake_run_scan(
        provider: PriceProvider, notifier: Notifier, settings: Settings, *, force: bool = False
    ) -> ScanResult:
        return _empty_result()

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    exit_code = cli._run_scan_command(_settings(), dry_run=True)

    assert exit_code == cli.EXIT_SUCCESS
