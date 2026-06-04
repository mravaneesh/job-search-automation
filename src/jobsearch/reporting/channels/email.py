"""Email notification channel (SMTP)."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from jobsearch.logging_config import get_logger
from jobsearch.reporting.channels.base import Channel, Message

log = get_logger("email")


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class EmailChannel(Channel):
    name = "email"

    def __init__(
        self,
        host: str | None,
        port: int,
        username: str | None,
        password: str | None,
        sender: str | None,
        recipients: list[str],
        use_tls: bool = True,
        timeout: float = 30.0,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._recipients = recipients
        self._use_tls = use_tls
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> EmailChannel:
        recipients = [r.strip() for r in (os.getenv("EMAIL_TO", "")).split(",") if r.strip()]
        return cls(
            host=os.getenv("SMTP_HOST"),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            sender=os.getenv("EMAIL_FROM") or os.getenv("SMTP_USERNAME"),
            recipients=recipients,
            use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        )

    def is_configured(self) -> bool:
        return bool(self._host and self._sender and self._recipients)

    def build_message(self, message: Message) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = message.subject
        msg["From"] = self._sender
        msg["To"] = ", ".join(self._recipients)
        msg.set_content(message.text)
        msg.add_alternative(f"<html><body>{message.html}</body></html>", subtype="html")
        return msg

    def send(self, message: Message) -> bool:
        if not self.is_configured():
            return False
        try:
            msg = self.build_message(message)
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
                if self._use_tls:
                    smtp.starttls()
                if self._username and self._password:
                    smtp.login(self._username, self._password)
                smtp.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError) as exc:  # never raise out of a channel
            log.warning("email_send_error", error=str(exc))
            return False
