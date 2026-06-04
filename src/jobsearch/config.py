"""Environment-driven settings. No secrets are hard-coded."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repository root (…/job-search-automation), resolved from this file's location.
ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
MIGRATIONS_DIR = ROOT / "migrations"


@dataclass(frozen=True)
class Settings:
    database_url: str
    http_timeout: float
    http_user_agent: str
    rate_limit_delay: float
    playwright_headless: bool
    playwright_nav_timeout_ms: int
    log_level: str


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql://jobsearch:jobsearch@localhost:5432/jobsearch"
        ),
        http_timeout=float(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
        http_user_agent=os.getenv(
            "HTTP_USER_AGENT",
            "job-search-automation/0.1 (+https://github.com/mravaneesh/job-search-automation)",
        ),
        rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY_SECONDS", "1.0")),
        playwright_headless=_get_bool("PLAYWRIGHT_HEADLESS", True),
        playwright_nav_timeout_ms=int(os.getenv("PLAYWRIGHT_NAV_TIMEOUT_MS", "30000")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
