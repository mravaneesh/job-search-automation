from jobsearch.reporting.channels.base import Message
from jobsearch.reporting.channels.email import EmailChannel
from jobsearch.reporting.channels.telegram import TelegramChannel
from jobsearch.reporting.repository import notification_fingerprint


def _message():
    return Message(
        subject="[Job Search] 2 new matches",
        text="plain body",
        html="<h2>body</h2>",
        telegram_html="<b>body</b>",
    )


def test_telegram_not_configured_without_credentials():
    assert TelegramChannel(token=None, chat_id=None).is_configured() is False
    assert TelegramChannel(token="t", chat_id="c").is_configured() is True


def test_telegram_payload():
    payload = TelegramChannel.build_payload("123", _message())
    assert payload["chat_id"] == "123"
    assert payload["parse_mode"] == "HTML"
    assert payload["disable_web_page_preview"] is True
    assert payload["text"] == "<b>body</b>"


def test_telegram_send_returns_false_when_unconfigured():
    # No network call should happen when not configured.
    assert TelegramChannel(token=None, chat_id=None).send(_message()) is False


def test_email_not_configured_without_host_or_recipients():
    assert EmailChannel(None, 587, None, None, None, []).is_configured() is False
    ch = EmailChannel("smtp.x", 587, "u", "p", "a@x.com", ["b@x.com"])
    assert ch.is_configured() is True


def test_email_message_is_multipart_with_html():
    ch = EmailChannel("smtp.x", 587, "u", "p", "from@x.com", ["to1@x.com", "to2@x.com"])
    msg = ch.build_message(_message())
    assert msg["Subject"] == "[Job Search] 2 new matches"
    assert msg["From"] == "from@x.com"
    assert msg["To"] == "to1@x.com, to2@x.com"
    assert msg.is_multipart()
    types = {part.get_content_type() for part in msg.iter_parts()}
    assert "text/plain" in types
    assert "text/html" in types


def test_fingerprint_changes_with_state():
    assert notification_fingerprint("HIGH", 90) == "HIGH:90"
    assert notification_fingerprint("HIGH", 90) != notification_fingerprint("HIGH", 91)
    assert notification_fingerprint("HIGH", 90) != notification_fingerprint("MEDIUM", 90)
