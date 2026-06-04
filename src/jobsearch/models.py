"""Canonical data models shared across collectors, normalization and storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

# Role categories targeted by Phase 1.
ROLE_ANDROID = "android"
ROLE_AI_ML = "ai_ml"
ROLE_BACKEND = "backend"
VALID_ROLES = {ROLE_ANDROID, ROLE_AI_ML, ROLE_BACKEND}


@dataclass
class RawJob:
    """A posting as returned by a collector, before normalization.

    Collectors are responsible only for faithful, deterministic extraction.
    Description is kept as HTML (``description_html``) or plain text
    (``description_text``); the normalizer produces the final plain text.
    """

    source: str
    company_name: str
    title: str
    url: str
    source_job_id: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description_html: str | None = None
    description_text: str | None = None
    created_date: date | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Job:
    """A normalized, deduplicated job ready for storage."""

    company_name: str
    role_category: str
    title: str
    source: str
    url: str
    fingerprint: str
    source_priority: int = 100
    source_job_id: str | None = None
    location: str | None = None
    experience: str | None = None
    employment_type: str | None = None
    description: str | None = None
    skills: list[str] = field(default_factory=list)
    created_date: date | None = None
    raw: dict[str, Any] = field(default_factory=dict)
