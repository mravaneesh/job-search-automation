"""Deterministic skill extraction driven by config/skills.yaml."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR


class SkillExtractor:
    def __init__(self, mapping: dict[str, list[re.Pattern[str]]]):
        self._mapping = mapping

    @classmethod
    def from_config(cls, path: Path | None = None) -> SkillExtractor:
        path = path or (CONFIG_DIR / "skills.yaml")
        data = yaml.safe_load(path.read_text()) or {}
        mapping: dict[str, list[re.Pattern[str]]] = {}
        for canonical, aliases in (data.get("skills") or {}).items():
            patterns = []
            for alias in aliases:
                alias = alias.strip()
                # Aliases may already be regex (e.g. "c\\+\\+"); wrap in word
                # boundaries unless they contain explicit surrounding spaces.
                if alias.startswith(" ") or alias.endswith(" "):
                    patterns.append(re.compile(alias.lower()))
                else:
                    patterns.append(re.compile(rf"(?<![a-z0-9]){alias.lower()}(?![a-z0-9])"))
            mapping[canonical] = patterns
        return cls(mapping)

    def extract(self, text: str | None) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        found = [
            canonical
            for canonical, patterns in self._mapping.items()
            if any(p.search(lowered) for p in patterns)
        ]
        return sorted(set(found))
