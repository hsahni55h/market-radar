"""Command-line entry point for Market Radar."""

import logging

from market_radar.config import get_settings
from market_radar.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the application foundation."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Market Radar started (env=%s, tz=%s)", settings.app_env, settings.timezone)


if __name__ == "__main__":
    main()
