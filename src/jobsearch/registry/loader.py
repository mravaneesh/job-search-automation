"""Load and validate the company / aggregator registry from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jobsearch.config import CONFIG_DIR

VALID_SOURCES = {"greenhouse", "lever", "ashby", "career_page"}
VALID_AGGREGATORS = {"linkedin", "indeed", "naukri", "wellfound"}
VALID_STATUS = {"implemented", "pending"}


@dataclass
class CompanyTarget:
    name: str
    category: str | None
    source: str
    status: str
    token: str | None = None
    spec: dict[str, Any] = field(default_factory=dict)

    @property
    def is_implemented(self) -> bool:
        return self.status == "implemented"


@dataclass
class AggregatorTarget:
    source: str
    status: str
    locations: list[str] = field(default_factory=list)

    @property
    def is_implemented(self) -> bool:
        return self.status == "implemented"


@dataclass
class Registry:
    companies: list[CompanyTarget]
    aggregators: list[AggregatorTarget]


def _validate_company(entry: dict[str, Any]) -> CompanyTarget:
    name = entry.get("name")
    source = entry.get("source")
    status = entry.get("status", "pending")
    if not name:
        raise ValueError(f"company entry missing 'name': {entry!r}")
    if source not in VALID_SOURCES:
        raise ValueError(f"company {name!r} has invalid source {source!r}")
    if status not in VALID_STATUS:
        raise ValueError(f"company {name!r} has invalid status {status!r}")
    if source in {"greenhouse", "lever", "ashby"} and status == "implemented" and not entry.get(
        "token"
    ):
        raise ValueError(f"company {name!r} is implemented on {source} but has no token")
    return CompanyTarget(
        name=name,
        category=entry.get("category"),
        source=source,
        status=status,
        token=entry.get("token"),
        spec=entry.get("spec", {}) or {},
    )


def _validate_aggregator(entry: dict[str, Any]) -> AggregatorTarget:
    source = entry.get("source")
    status = entry.get("status", "pending")
    if source not in VALID_AGGREGATORS:
        raise ValueError(f"aggregator has invalid source {source!r}")
    if status not in VALID_STATUS:
        raise ValueError(f"aggregator {source!r} has invalid status {status!r}")
    return AggregatorTarget(
        source=source, status=status, locations=list(entry.get("locations", []))
    )


def load_registry(path: Path | None = None) -> Registry:
    path = path or (CONFIG_DIR / "companies.yaml")
    data = yaml.safe_load(path.read_text()) or {}
    companies = [_validate_company(e) for e in data.get("companies", [])]
    aggregators = [_validate_aggregator(e) for e in data.get("aggregators", [])]

    names = [c.name for c in companies]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise ValueError(f"duplicate company names in registry: {sorted(dupes)}")

    return Registry(companies=companies, aggregators=aggregators)
