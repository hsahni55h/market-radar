"""Discord webhook alert delivery."""

import logging
from collections.abc import Callable
from time import sleep
from typing import Never

import httpx
from pydantic import SecretStr

from market_radar.alerts.message import AlertMessage, AlertSection

logger = logging.getLogger(__name__)

MAX_EMBED_TITLE_LENGTH = 256
MAX_EMBED_FIELD_NAME_LENGTH = 256
MAX_EMBED_FIELD_VALUE_LENGTH = 1024
MAX_EMBED_FOOTER_LENGTH = 2048


class DiscordNotificationError(RuntimeError):
    """Raised when a Discord alert cannot be delivered."""


class DiscordNotifier:
    """Deliver alert messages through a Discord webhook."""

    def __init__(
        self,
        webhook_url: SecretStr,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
        max_attempts: int = 2,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        """Initialize a notifier with a secret webhook URL and optional HTTP client."""
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self._webhook_url = webhook_url
        self._client = client or httpx.Client()
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleeper = sleeper

    def send(self, message: AlertMessage) -> None:
        """Post a Discord embed, retrying transient failures once by default."""
        payload = build_payload(message)
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._client.post(
                    self._webhook_url.get_secret_value(),
                    json=payload,
                    timeout=self._timeout_seconds,
                )
            except httpx.RequestError:
                if attempt == self._max_attempts:
                    self._raise_delivery_error()
                logger.warning("Discord delivery failed on attempt %d; retrying", attempt)
                self._sleeper(1.0)
                continue

            if response.is_success:
                return
            if response.status_code == 429 and attempt < self._max_attempts:
                delay_seconds = _retry_after_seconds(response)
                logger.warning("Discord rate limited alert delivery; retrying")
                self._sleeper(delay_seconds)
                continue
            if response.status_code >= 500 and attempt < self._max_attempts:
                logger.warning("Discord service error on attempt %d; retrying", attempt)
                self._sleeper(1.0)
                continue

            self._raise_delivery_error()

    def _raise_delivery_error(self) -> Never:
        logger.error("Discord alert delivery failed")
        raise DiscordNotificationError("Discord alert delivery failed") from None


def build_payload(message: AlertMessage) -> dict[str, object]:
    """Render an alert message as a size-limited Discord embed payload."""
    embed: dict[str, object] = {
        "title": message.title[:MAX_EMBED_TITLE_LENGTH],
        "fields": [_section_payload(section) for section in message.sections[:25]],
        "footer": {"text": message.footer[:MAX_EMBED_FOOTER_LENGTH]},
    }
    if message.timestamp is not None:
        embed["timestamp"] = message.timestamp.isoformat()
    return {"embeds": [embed]}


def _section_payload(section: AlertSection) -> dict[str, object]:
    lines = "\n".join(section.lines) or "No data."
    return {
        "name": section.heading[:MAX_EMBED_FIELD_NAME_LENGTH],
        "value": lines[:MAX_EMBED_FIELD_VALUE_LENGTH],
        "inline": False,
    }


def _retry_after_seconds(response: httpx.Response) -> float:
    try:
        return max(float(response.headers.get("Retry-After", "1")), 0.0)
    except ValueError:
        return 1.0
