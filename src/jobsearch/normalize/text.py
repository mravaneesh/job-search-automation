"""Deterministic HTML -> plain text conversion (no LLM)."""

from __future__ import annotations

import html
import re

from selectolax.parser import HTMLParser

_WS = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def html_to_text(value: str | None) -> str | None:
    """Convert an HTML fragment to readable plain text.

    Block-level tags become newlines so structure is preserved enough for
    downstream keyword matching. Returns None for empty input.
    """
    if not value:
        return None
    # Some APIs (e.g. Greenhouse) HTML-escape the content field once.
    unescaped = html.unescape(value)
    tree = HTMLParser(unescaped)
    for tag in tree.css("script, style"):
        tag.decompose()
    text = tree.body.text(separator="\n") if tree.body else tree.text(separator="\n")
    if text is None:
        return None
    lines = [_WS.sub(" ", line).strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    cleaned = _BLANK_LINES.sub("\n\n", cleaned).strip()
    return cleaned or None
