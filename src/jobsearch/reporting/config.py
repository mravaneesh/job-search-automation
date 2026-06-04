"""Reporting configuration (behaviour from YAML; secrets from env)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from jobsearch.config import CONFIG_DIR


@dataclass
class ReportingConfig:
    top_opportunities: int
    notify_priorities: list[str]
    roles: list[str]
    role_labels: dict[str, str] = field(default_factory=dict)

    def label(self, role: str) -> str:
        return self.role_labels.get(role, role)

    @classmethod
    def from_config(cls, path: Path | None = None) -> ReportingConfig:
        path = path or (CONFIG_DIR / "reporting.yaml")
        data = yaml.safe_load(path.read_text()) or {}
        return cls(
            top_opportunities=int(data.get("top_opportunities", 10)),
            notify_priorities=list(data.get("notify_priorities") or ["HIGH", "MEDIUM"]),
            roles=list(data.get("roles") or ["android", "backend", "ai_ml"]),
            role_labels=dict(data.get("role_labels") or {}),
        )
