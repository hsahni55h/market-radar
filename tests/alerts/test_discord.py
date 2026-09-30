"""Tests for Discord webhook alert delivery."""

import logging
from datetime import UTC, datetime
from typing import cast

import httpx
import pytest
from pydantic import SecretStr

from market_radar.alerts.discord import (
    DiscordNotificationError,
    DiscordNotifier,
    build_payload,
)
from market_radar.alerts.message import AlertMessage, AlertSection
from market_radar.logging_config import configure_logging


def message() -> AlertMessage:
    """Create a representative formatted alert message."""
    return AlertMessage(
        title="Nifty 500 Market Movers",
        sections=(
            AlertSection("Top Gainers", ("GAIN: Rs. 1,234.50 (+23.45%)",)),
            AlertSection("Top Losers", ("LOSS: Rs. 800.00 (-20.00%)",)),
        ),
        footer="Scanned: 499 | Skipped: 2",
        timestamp=datetime(2026, 9, 30, 15, 45, tzinfo=UTC),
    )


def test_build_payload_creates_discord_embed() -> None:
    """Formatted messages become a Discord-compatible embed payload."""
    payload = build_payload(message())

    assert payload == {
        "embeds": [
            {
                "title": "Nifty 500 Market Movers",
                "fields": [
                    {
                        "name": "Top Gainers",
                        "value": "GAIN: Rs. 1,234.50 (+23.45%)",
                        "inline": False,
                    },
                    {
                        "name": "Top Losers",
                        "value": "LOSS: Rs. 800.00 (-20.00%)",
                        "inline": False,
                    },
                ],
                "footer": {"text": "Scanned: 499 | Skipped: 2"},
                "timestamp": "2026-09-30T15:45:00+00:00",
            }
        ]
    }


def test_build_payload_limits_discord_embed_fields() -> None:
    """Long message content is constrained to Discord's embed limits."""
    payload = build_payload(
        AlertMessage(
            title="T" * 257,
            sections=(AlertSection("H" * 257, ("L" * 1_025,)),),
            footer="F" * 2_049,
            timestamp=None,
        )
    )

    embeds = cast(list[dict[str, object]], payload["embeds"])
    embed = embeds[0]
    fields = cast(list[dict[str, object]], embed["fields"])
    footer = cast(dict[str, str], embed["footer"])

    assert len(cast(str, embed["title"])) == 256
    assert len(cast(str, fields[0]["name"])) == 256
    assert len(cast(str, fields[0]["value"])) == 1024
    assert len(footer["text"]) == 2048
    assert "timestamp" not in embed


def test_notifier_retries_rate_limited_request() -> None:
    """A rate-limited webhook request waits for Retry-After and retries once."""
    responses = iter((httpx.Response(429, headers={"Retry-After": "0.5"}), httpx.Response(204)))
    client = httpx.Client(transport=httpx.MockTransport(lambda request: next(responses)))
    delays: list[float] = []
    notifier = DiscordNotifier(
        SecretStr("https://discord.com/api/webhooks/id/token"),
        client=client,
        sleeper=delays.append,
    )

    notifier.send(message())

    assert delays == [0.5]


def test_notifier_logs_and_raises_without_exposing_webhook_url(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failed delivery stays clear and secret-free in both logs and exceptions."""
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    notifier = DiscordNotifier(
        SecretStr("https://discord.com/api/webhooks/id/token"),
        client=client,
        max_attempts=1,
    )

    with caplog.at_level("ERROR"), pytest.raises(DiscordNotificationError) as error:
        notifier.send(message())

    assert str(error.value) == "Discord alert delivery failed"
    assert error.value.__cause__ is None
    assert "Discord alert delivery failed" in caplog.text
    assert "https://discord.com" not in str(error.value)
    assert "https://discord.com" not in caplog.text


def test_notifier_hides_webhook_url_when_connection_is_reset(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A network reset does not retain the secret-bearing HTTP request exception."""
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(
                httpx.ConnectError("Connection reset by peer", request=request)
            )
        )
    )
    notifier = DiscordNotifier(
        SecretStr("https://discord.com/api/webhooks/id/token"),
        client=client,
        max_attempts=1,
    )

    with caplog.at_level("ERROR"), pytest.raises(DiscordNotificationError) as error:
        notifier.send(message())

    assert error.value.__cause__ is None
    assert "https://discord.com" not in str(error.value)
    assert "https://discord.com" not in caplog.text


def test_configure_logging_keeps_webhook_url_out_of_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """httpx request logging never emits the webhook URL, even at INFO level."""
    webhook = "https://discord.com/api/webhooks/secret-id/secret-token"
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(204)))
    notifier = DiscordNotifier(SecretStr(webhook), client=client)

    configure_logging("INFO")
    with caplog.at_level(logging.INFO):
        notifier.send(message())

    assert "secret-id" not in caplog.text
    assert "secret-token" not in caplog.text
    for record in caplog.records:
        rendered = record.getMessage()
        assert webhook not in rendered
        assert "secret-id" not in rendered
        assert "secret-token" not in rendered
