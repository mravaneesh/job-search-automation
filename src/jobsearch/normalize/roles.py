"""Deterministic role classification driven by config/roles.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR


@dataclass
class _RoleRule:
    name: str
    title_patterns: list[re.Pattern[str]]
    description_patterns: list[re.Pattern[str]]


def _compile(keywords: list[str]) -> list[re.Pattern[str]]:
    patterns = []
    for kw in keywords:
        # Word-boundary, case-insensitive. Keywords may contain spaces.
        patterns.append(re.compile(rf"(?<![a-z0-9]){re.escape(kw.lower())}(?![a-z0-9])"))
    return patterns


class RoleClassifier:
    def __init__(self, priority: list[str], rules: dict[str, _RoleRule]):
        self._priority = priority
        self._rules = rules

    @classmethod
    def from_config(cls, path: Path | None = None) -> RoleClassifier:
        path = path or (CONFIG_DIR / "roles.yaml")
        data = yaml.safe_load(path.read_text()) or {}
        priority = data.get("priority", [])
        rules: dict[str, _RoleRule] = {}
        for name, cfg in (data.get("roles") or {}).items():
            rules[name] = _RoleRule(
                name=name,
                title_patterns=_compile(cfg.get("title_keywords", [])),
                description_patterns=_compile(cfg.get("description_keywords", [])),
            )
        if not priority:
            priority = list(rules)
        return cls(priority=priority, rules=rules)

    def classify(self, title: str, description: str | None = None) -> str | None:
        """Return the role category, or None if no target role matches.

        Title matches take precedence; the description is only consulted when no
        title matched. Roles are evaluated in configured priority order.
        """
        title_l = (title or "").lower()
        for name in self._priority:
            rule = self._rules.get(name)
            if rule and any(p.search(title_l) for p in rule.title_patterns):
                return name

        if description:
            desc_l = description.lower()
            for name in self._priority:
                rule = self._rules.get(name)
                if rule and any(p.search(desc_l) for p in rule.description_patterns):
                    return name
        return None
