"""Deterministic location filter driven by config/locations.yaml.

Keeps a posting only when its location is in India **or** remote-eligible;
everything else (foreign on-site) is dropped during normalization. Matching is
word-boundary and case-insensitive so a country code like ``IND`` matches but
``Indiana`` / ``Indonesia`` do not.

``remote_scope`` controls how strict the remote rule is:

* ``any``   — keep every remote role (e.g. "Remote - USA" is kept).
* ``india`` — keep a remote role only when it is global/anywhere or not tied to
  a specific foreign geography. "Remote - USA" / "Remote, Brazil" are dropped;
  "Remote", "Anywhere", "Remote - India" are kept.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR

# Placeholders that mean "no usable location" rather than a real place.
_UNKNOWN = {"", "n/a", "na", "none", "unknown", "-", "tbd"}

_WORD = re.compile(r"[a-z]+")


def _compile(keywords: list[str]) -> list[re.Pattern[str]]:
    return [
        re.compile(rf"(?<![a-z0-9]){re.escape(kw.lower())}(?![a-z0-9])") for kw in keywords
    ]


def _words(keywords: list[str]) -> set[str]:
    """Flatten keyword phrases into their individual lowercase words."""
    out: set[str] = set()
    for kw in keywords:
        out.update(_WORD.findall(kw.lower()))
    return out


@dataclass
class LocationFilter:
    enabled: bool
    keep_unknown: bool
    remote_scope: str
    remote_patterns: list[re.Pattern[str]]
    india_patterns: list[re.Pattern[str]]
    global_patterns: list[re.Pattern[str]]
    noise_words: set[str]

    @classmethod
    def from_config(cls, path: Path | None = None) -> LocationFilter:
        path = path or (CONFIG_DIR / "locations.yaml")
        if not path.exists():
            # No config -> permissive (keep everything), preserving old behaviour.
            return cls(
                enabled=False,
                keep_unknown=True,
                remote_scope="any",
                remote_patterns=[],
                india_patterns=[],
                global_patterns=[],
                noise_words=set(),
            )
        data = yaml.safe_load(path.read_text()) or {}
        remote_kw = data.get("remote_keywords", [])
        global_kw = data.get("global_remote_keywords", [])
        extra_noise = data.get("remote_noise_words", [])
        return cls(
            enabled=bool(data.get("enabled", True)),
            keep_unknown=bool(data.get("keep_unknown_location", True)),
            remote_scope=str(data.get("remote_scope", "any")).lower(),
            remote_patterns=_compile(remote_kw),
            india_patterns=_compile(data.get("india_keywords", [])),
            global_patterns=_compile(global_kw),
            # Words that don't, on their own, denote a foreign geography.
            noise_words=_words(remote_kw) | _words(global_kw) | _words(extra_noise),
        )

    def keep(self, location: str | None) -> bool:
        """True if the posting should be kept under the location policy."""
        if not self.enabled:
            return True
        loc = (location or "").strip().lower()
        if loc in _UNKNOWN:
            return self.keep_unknown
        if any(p.search(loc) for p in self.india_patterns):
            return True
        if not any(p.search(loc) for p in self.remote_patterns):
            return False  # foreign on-site
        # Remote role.
        if self.remote_scope != "india":
            return True
        # India scope: keep only if global/anywhere or no foreign geo is named.
        if any(p.search(loc) for p in self.global_patterns):
            return True
        return set(_WORD.findall(loc)).issubset(self.noise_words)
