"""Candidate profile and scoring configuration loaders."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR


@dataclass
class Profile:
    experience_years: float
    role_priority: dict[str, str]          # role -> tier (primary/secondary/stretch)
    preferred_locations: list[str]
    skills_by_role: dict[str, list[str]]
    # Derived: lowercased skill -> canonical display, across all roles.
    skills_display: dict[str, str] = field(default_factory=dict)

    @property
    def all_skills_lower(self) -> set[str]:
        return set(self.skills_display)

    def tier_for(self, role: str) -> str:
        return self.role_priority.get(role, "stretch")

    @classmethod
    def from_config(cls, path: Path | None = None) -> Profile:
        path = path or (CONFIG_DIR / "profile.yaml")
        data = yaml.safe_load(path.read_text()) or {}
        skills_by_role = {r: list(s or []) for r, s in (data.get("skills") or {}).items()}
        display: dict[str, str] = {}
        for skills in skills_by_role.values():
            for skill in skills:
                display[skill.lower()] = skill
        return cls(
            experience_years=float(data.get("experience_years", 0)),
            role_priority=dict(data.get("role_priority") or {}),
            preferred_locations=list(data.get("preferred_locations") or []),
            skills_by_role=skills_by_role,
            skills_display=display,
        )


@dataclass
class ScoringConfig:
    scorer_version: int
    use_llm: bool
    model: str
    batch_size: int
    max_tokens_per_day: int
    weights: dict[str, float]
    priority_thresholds: dict[str, int]
    role_priority_factor: dict[str, float]
    company_quality: dict[str, int]

    @classmethod
    def from_config(cls, path: Path | None = None) -> ScoringConfig:
        path = path or (CONFIG_DIR / "scoring.yaml")
        data = yaml.safe_load(path.read_text()) or {}
        return cls(
            scorer_version=int(data.get("scorer_version", 1)),
            use_llm=bool(data.get("use_llm", False)),
            model=str(data.get("model", "claude-opus-4-8")),
            batch_size=int(data.get("batch_size", 15)),
            max_tokens_per_day=int(data.get("max_tokens_per_day", 20000)),
            weights=dict(data.get("weights") or {}),
            priority_thresholds=dict(data.get("priority_thresholds") or {}),
            role_priority_factor=dict(data.get("role_priority_factor") or {}),
            company_quality=dict(data.get("company_quality") or {}),
        )
