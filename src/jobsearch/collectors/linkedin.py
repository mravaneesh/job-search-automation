"""LinkedIn aggregator collector (Playwright, best-effort).

Uses the public guest jobs search page. Markup changes often; the parser skips
any card that is missing a title or link rather than guessing.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from selectolax.parser import HTMLParser

from jobsearch.collectors.aggregator_base import AggregatorCollector
from jobsearch.models import RawJob


class LinkedInCollector(AggregatorCollector):
    source = "linkedin"

    def build_url(self, query: str, location: str) -> str:
        return (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote_plus(query)}&location={quote_plus(location)}&start=0"
        )

    @staticmethod
    def parse(html: str, company_hint: str | None = None) -> list[RawJob]:
        tree = HTMLParser(html or "")
        jobs: list[RawJob] = []
        for card in tree.css("div.base-card"):
            title_el = card.css_first(".base-search-card__title")
            link_el = card.css_first("a.base-card__full-link")
            if not title_el or not link_el:
                continue
            url = (link_el.attributes.get("href") or "").split("?")[0]
            title = title_el.text(strip=True)
            if not title or not url:
                continue
            company_el = card.css_first(".base-search-card__subtitle")
            location_el = card.css_first(".job-search-card__location")
            jobs.append(
                RawJob(
                    source="linkedin",
                    company_name=(company_el.text(strip=True) if company_el else "")
                    or (company_hint or "Unknown"),
                    title=title,
                    url=url,
                    location=location_el.text(strip=True) if location_el else None,
                )
            )
        return jobs
