"""Deterministic seniority / experience filter (config/experience.yaml).

Drops postings that are too senior for the candidate — managerial titles
(Engineering Manager, Director, Head, VP), senior-IC titles well above the
candidate's level (Staff, Principal, Architect), and postings that explicitly
require more years than ``max_required_years``. Matching is word-boundary and
case-insensitive so "Staff" matches but "Stafford" does not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR

# Min years from "5+ years", "5-8 years", "5 to 8 years", "5 yrs" — lower bound.
_YEARS = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:(?:-|to|–|—)\s*\d{1,2}\s*)?(?:years?|yrs?)", re.IGNORECASE
)


def _compile(keywords: list[str]) -> list[re.Pattern[str]]:
    return [
        re.compile(rf"(?<![a-z0-9]){re.escape(kw.lower())}(?![a-z0-9])") for kw in keywords
    ]


@dataclass
class SeniorityFilter:
    enabled: bool
    max_required_years: int | None
    exclude_patterns: list[re.Pattern[str]]

    @classmethod
    def from_config(cls, path: Path | None = None) -> SeniorityFilter:
        path = path or (CONFIG_DIR / "experience.yaml")
        if not path.exists():
            return cls(enabled=False, max_required_years=None, exclude_patterns=[])
        data = yaml.safe_load(path.read_text()) or {}
        max_years = data.get("max_required_years")
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_required_years=int(max_years) if max_years is not None else None,
            exclude_patterns=_compile(data.get("exclude_title_keywords", [])),
        )

    def keep(self, title: str, description: str | None = None) -> bool:
        """True if the posting is at/under the candidate's level."""
        if not self.enabled:
            return True
        title_l = (title or "").lower()
        # "Member of Technical Staff" (MTS) is a standard IC title at AI labs
        # (OpenAI, Anthropic, xAI, DevRev), not a seniority level — neutralise the
        # "staff" token so it isn't mistaken for a Staff-level role.
        checked = title_l.replace("technical staff", "technical ic")
        if any(p.search(checked) for p in self.exclude_patterns):
            return False
        if self.max_required_years is not None:
            # Prefer an explicit requirement in the title, else the description.
            for text in (title_l, (description or "").lower()):
                m = _YEARS.search(text)
                if m and int(m.group(1)) > self.max_required_years:
                    return False
                if m:
                    break
        return True
