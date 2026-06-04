"""Channel protocol and the message payload."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class Message:
    subject: str
    text: str            # plain-text body
    html: str            # rich HTML body (email)
    telegram_html: str   # Telegram-flavoured HTML body


class Channel(abc.ABC):
    name: str

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """True when this channel has the credentials it needs."""

    @abc.abstractmethod
    def send(self, message: Message) -> bool:
        """Deliver the message. Returns True on success; never raises."""
