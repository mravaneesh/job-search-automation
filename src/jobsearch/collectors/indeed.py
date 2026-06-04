"""Indeed aggregator collector (Playwright, best-effort)."""

from __future__ import annotations

from urllib.parse import quote_plus

from selectolax.parser import HTMLParser

from jobsearch.collectors.aggregator_base import AggregatorCollector
from jobsearch.models import RawJob

_BASE = "https://www.indeed.com"


class IndeedCollector(AggregatorCollector):
    source = "indeed"

    def build_url(self, query: str, location: str) -> str:
        return f"{_BASE}/jobs?q={quote_plus(query)}&l={quote_plus(location)}"

    @staticmethod
    def parse(html: str, company_hint: str | None = None) -> list[RawJob]:
        tree = HTMLParser(html or "")
        jobs: list[RawJob] = []
        for card in tree.css("div.job_seen_beacon, div.cardOutline"):
            title_el = card.css_first("h2.jobTitle span") or card.css_first("h2.jobTitle a")
            link_el = card.css_first("a.jcs-JobTitle") or card.css_first("h2.jobTitle a")
            if not title_el or not link_el:
                continue
            href = link_el.attributes.get("href") or ""
            url = href if href.startswith("http") else _BASE + href
            title = title_el.text(strip=True)
            if not title:
                continue
            company_el = card.css_first('[data-testid="company-name"]') or card.css_first(
                "span.companyName"
            )
            loc_el = card.css_first('[data-testid="text-location"]') or card.css_first(
                "div.companyLocation"
            )
            jobs.append(
                RawJob(
                    source="indeed",
                    company_name=(company_el.text(strip=True) if company_el else "")
                    or (company_hint or "Unknown"),
                    title=title,
                    url=url,
                    location=loc_el.text(strip=True) if loc_el else None,
                )
            )
        return jobs
