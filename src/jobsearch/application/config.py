"""Configuration loaders for application intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR


@dataclass
class Candidate:
    name: str
    email: str
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    headline: str = ""
    summary: str = ""

    @classmethod
    def from_config(cls, path: Path | None = None) -> Candidate:
        data = yaml.safe_load((path or CONFIG_DIR / "candidate.yaml").read_text()) or {}
        return cls(
            name=data.get("name", "Candidate"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            location=data.get("location", ""),
            linkedin=data.get("linkedin", ""),
            github=data.get("github", ""),
            headline=data.get("headline", ""),
            summary=(data.get("summary", "") or "").strip(),
        )


@dataclass
class CompanyTiers:
    default: str
    tier_members: dict[str, set[str]]  # tier -> {lowercased company names}
    labels: dict[str, str]

    def tier_for(self, company_name: str | None) -> str:
        name = (company_name or "").strip().lower()
        for tier, members in self.tier_members.items():
            if name in members:
                return tier
        return self.default

    def label(self, tier: str | None) -> str:
        return self.labels.get(tier or self.default, tier or self.default)

    @classmethod
    def from_config(cls, path: Path | None = None) -> CompanyTiers:
        data = yaml.safe_load((path or CONFIG_DIR / "company_tiers.yaml").read_text()) or {}
        members = {
            tier: {str(n).strip().lower() for n in names}
            for tier, names in (data.get("tiers") or {}).items()
        }
        return cls(
            default=data.get("default", "tier3"),
            tier_members=members,
            labels=dict(data.get("labels") or {}),
        )


@dataclass
class ApplicationConfig:
    generate_only_priority: str
    cover_letter_min_score: int
    cover_letter_require_priority: str
    strategy_apply_immediately: int
    strategy_strong_apply: int
    use_llm: bool
    model: str
    max_tokens_per_day: int
    bullet_suggestions: int

    @classmethod
    def from_config(cls, path: Path | None = None) -> ApplicationConfig:
        data = yaml.safe_load((path or CONFIG_DIR / "application.yaml").read_text()) or {}
        cover = data.get("cover_letter") or {}
        strat = data.get("strategy") or {}
        return cls(
            generate_only_priority=data.get("generate_only_priority", "HIGH"),
            cover_letter_min_score=int(cover.get("min_match_score", 80)),
            cover_letter_require_priority=cover.get("require_priority", "HIGH"),
            strategy_apply_immediately=int(strat.get("apply_immediately", 85)),
            strategy_strong_apply=int(strat.get("strong_apply", 72)),
            use_llm=bool(data.get("use_llm", False)),
            model=str(data.get("model", "claude-opus-4-8")),
            max_tokens_per_day=int(data.get("max_tokens_per_day", 20000)),
            bullet_suggestions=int(data.get("bullet_suggestions", 4)),
        )


@dataclass
class ResumeSpec:
    role_category: str
    name: str
    version: int
    focus_skills: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    file_path: str | None = None
    notes: str | None = None
