"""Small deterministic parsing helpers shared by collectors."""

from __future__ import annotations

from datetime import UTC, date, datetime


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        # Handle trailing Z and offsets.
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        # Fall back to a plain date prefix (YYYY-MM-DD…).
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def parse_epoch_ms(value: int | float | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000.0, tz=UTC).date()
    except (ValueError, OverflowError, OSError):
        return None


_LOOSE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%d %b %Y", "%m/%d/%Y", "%d-%m-%Y")


def parse_loose_date(value: str | None) -> date | None:
    """Parse a date that may be ISO or one of several human formats."""
    if not value:
        return None
    iso = parse_iso_date(value)
    if iso:
        return iso
    for fmt in _LOOSE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def get_path(data: dict, dotted: str):
    """Resolve a dotted path within nested dicts, returning None if missing."""
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur
