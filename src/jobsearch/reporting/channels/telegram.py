"""Telegram notification channel (Bot API sendMessage)."""

from __future__ import annotations

import os

import httpx

from jobsearch.logging_config import get_logger
from jobsearch.reporting.channels.base import Channel, Message

log = get_logger("telegram")

_API = "https://api.telegram.org/bot{token}/sendMessage"
_MAX_LEN = 4096  # Telegram message length limit


class TelegramChannel(Channel):
    name = "telegram"

    def __init__(self, token: str | None, chat_id: str | None, timeout: float = 20.0):
        self._token = token
        self._chat_id = chat_id
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> TelegramChannel:
        return cls(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))

    def is_configured(self) -> bool:
        return bool(self._token and self._chat_id)

    @staticmethod
    def build_payload(chat_id: str, message: Message) -> dict:
        body = message.telegram_html[:_MAX_LEN]
        return {
            "chat_id": chat_id,
            "text": body,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

    def send(self, message: Message) -> bool:
        if not self.is_configured():
            return False
        try:
            resp = httpx.post(
                _API.format(token=self._token),
                json=self.build_payload(self._chat_id, message),
                timeout=self._timeout,
            )
            if resp.is_success:
                return True
            log.warning("telegram_send_failed", status=resp.status_code, body=resp.text[:200])
        except httpx.HTTPError as exc:  # never raise out of a channel
            log.warning("telegram_send_error", error=str(exc))
        return False
