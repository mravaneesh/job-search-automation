"""Wellfound (AngelList Talent) aggregator collector (Playwright, best-effort)."""

from __future__ import annotations

from urllib.parse import quote_plus

from selectolax.parser import HTMLParser

from jobsearch.collectors.aggregator_base import AggregatorCollector
from jobsearch.models import RawJob

_BASE = "https://wellfound.com"


class WellfoundCollector(AggregatorCollector):
    source = "wellfound"

    def build_url(self, query: str, location: str) -> str:
        return f"{_BASE}/role/r/{quote_plus(query.lower().replace(' ', '-'))}"

    @staticmethod
    def parse(html: str, company_hint: str | None = None) -> list[RawJob]:
        tree = HTMLParser(html or "")
        jobs: list[RawJob] = []
        for card in tree.css('[data-test="JobListingCard"], div.styles_component__job'):
            link_el = card.css_first("a[href*='/jobs/']")
            if not link_el:
                continue
            href = link_el.attributes.get("href") or ""
            url = href if href.startswith("http") else _BASE + href
            title = link_el.text(strip=True)
            if not title or not url:
                continue
            company_el = card.css_first('[data-test="StartupResult"]') or card.css_first(
                "h2.company-name"
            )
            loc_el = card.css_first('[data-test="JobLocation"]')
            jobs.append(
                RawJob(
                    source="wellfound",
                    company_name=(company_el.text(strip=True) if company_el else "")
                    or (company_hint or "Unknown"),
                    title=title,
                    url=url,
                    location=loc_el.text(strip=True) if loc_el else None,
                )
            )
        return jobs
