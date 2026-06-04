"""Deterministic deduplication.

Two layers:
  * intra-source: the (source, source_job_id) index lets re-runs find the same
    posting; the canonical dedup key below subsumes it.
  * cross-source: a content fingerprint over company + normalized title +
    location, so the same role discovered on a career page and on an ATS
    collapses to one row.
"""

from __future__ import annotations

import hashlib
import re

# Seniority / noise tokens stripped from titles so that "Senior Backend
# Engineer" and "Backend Engineer" at the same company/location collapse.
_NOISE = {
    "senior",
    "sr",
    "junior",
    "jr",
    "staff",
    "principal",
    "lead",
    "ii",
    "iii",
    "iv",
    "i",
    "intern",
    "internship",
    "contract",
    "remote",
}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    lowered = _NON_ALNUM.sub(" ", text.lower()).strip()
    tokens = [t for t in lowered.split() if t not in _NOISE]
    return " ".join(tokens)


def fingerprint(company: str, title: str, location: str | None) -> str:
    """Stable cross-source dedup key."""
    parts = [_normalize(company), _normalize(title), _normalize(location)]
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
