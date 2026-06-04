"""Notification channels. Each is configured from environment variables and
skips gracefully when its credentials are absent."""

from __future__ import annotations

from jobsearch.reporting.channels.base import Channel, Message
from jobsearch.reporting.channels.email import EmailChannel
from jobsearch.reporting.channels.telegram import TelegramChannel


def build_channels(only: set[str] | None = None) -> list[Channel]:
    """All known channels, optionally filtered by name."""
    channels: list[Channel] = [TelegramChannel.from_env(), EmailChannel.from_env()]
    if only:
        channels = [c for c in channels if c.name in only]
    return channels


__all__ = ["Channel", "Message", "EmailChannel", "TelegramChannel", "build_channels"]
