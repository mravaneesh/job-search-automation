"""Base for Playwright-driven aggregator collectors.

Aggregators (LinkedIn, Indeed, Naukri, Wellfound) are searched by role query
rather than per company. They are brittle by nature (anti-bot defences, ToS
limits, frequently changing markup), so they are deterministic best-effort:

  * ``parse(html, ...)`` is a PURE function over a results HTML string. It is
    what unit tests exercise, using saved fixtures — no browser, no network.
  * ``search(...)`` drives Playwright to obtain that HTML. Playwright is
    imported lazily so the rest of the system (and tests) run without browsers.

No LLM is used anywhere: extraction is CSS-selector based via selectolax.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable

from jobsearch.config import Settings
from jobsearch.models import RawJob

# Search queries used for each target role.
ROLE_QUERIES = {
    "android": "Android Engineer",
    "backend": "Backend Engineer",
    "ai_ml": "Machine Learning Engineer",
}


class AggregatorCollector(abc.ABC):
    source: str

    def __init__(self, settings: Settings):
        self._settings = settings

    @staticmethod
    @abc.abstractmethod
    def parse(html: str, company_hint: str | None = None) -> list[RawJob]:
        """Parse a search-results HTML page into RawJob objects."""
        raise NotImplementedError

    @abc.abstractmethod
    def build_url(self, query: str, location: str) -> str:
        """Build the search URL for a role query + location."""
        raise NotImplementedError

    def search(self, query: str, location: str) -> Iterable[RawJob]:
        """Fetch the search page with Playwright and parse it."""
        html = self._fetch_html(self.build_url(query, location))
        return self.parse(html)

    def _fetch_html(self, url: str) -> str:
        # Lazy import so Playwright is only required when actually scraping.
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self._settings.playwright_headless)
            try:
                page = browser.new_page(user_agent=self._settings.http_user_agent)
                page.set_default_navigation_timeout(self._settings.playwright_nav_timeout_ms)
                page.goto(url, wait_until="domcontentloaded")
                return page.content()
            finally:
                browser.close()
