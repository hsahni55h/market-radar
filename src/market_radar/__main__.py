"""Command-line entry point for Market Radar."""

import argparse
import logging
import sys

from market_radar.alerts.base import Notifier
from market_radar.alerts.console import ConsoleNotifier
from market_radar.alerts.discord import DiscordNotificationError, DiscordNotifier
from market_radar.config import Settings, get_settings
from market_radar.logging_config import configure_logging
from market_radar.providers.yfinance_provider import YFinancePriceProvider
from market_radar.run_scan import run_scan

logger = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CONFIG_ERROR = 2


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing for a command."""


def main() -> int:
    """Parse arguments and dispatch to the requested command."""
    settings = get_settings()
    configure_logging(settings.log_level)

    parser = argparse.ArgumentParser(prog="market_radar")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser("scan", help="Scan the universe and deliver an alert.")
    scan_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the alert to the console instead of sending it to Discord.",
    )
    args = parser.parse_args()

    if args.command == "scan":
        return _run_scan_command(settings, dry_run=bool(args.dry_run))
    return EXIT_FAILURE


def _run_scan_command(settings: Settings, *, dry_run: bool) -> int:
    provider = YFinancePriceProvider()
    try:
        notifier = _build_notifier(settings, dry_run=dry_run)
    except ConfigurationError as error:
        logger.error("Cannot run scan: %s", error)
        return EXIT_CONFIG_ERROR

    try:
        run_scan(provider, notifier, settings)
    except DiscordNotificationError as error:
        logger.error("Alert delivery failed: %s", error)
        return EXIT_FAILURE
    except Exception:
        logger.exception("Scan failed")
        return EXIT_FAILURE
    return EXIT_SUCCESS


def _build_notifier(settings: Settings, *, dry_run: bool) -> Notifier:
    if dry_run:
        return ConsoleNotifier()
    if settings.discord_webhook_url is None:
        raise ConfigurationError("DISCORD_WEBHOOK_URL is not set; use --dry-run to print instead")
    return DiscordNotifier(settings.discord_webhook_url)


if __name__ == "__main__":
    sys.exit(main())
