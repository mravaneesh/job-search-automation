"""Naukri aggregator collector (Playwright, best-effort)."""

from __future__ import annotations

from selectolax.parser import HTMLParser

from jobsearch.collectors.aggregator_base import AggregatorCollector
from jobsearch.models import RawJob


class NaukriCollector(AggregatorCollector):
    source = "naukri"

    def build_url(self, query: str, location: str) -> str:
        slug = query.lower().replace(" ", "-")
        loc = location.lower().replace(" ", "-")
        return f"https://www.naukri.com/{slug}-jobs-in-{loc}"

    @staticmethod
    def parse(html: str, company_hint: str | None = None) -> list[RawJob]:
        tree = HTMLParser(html or "")
        jobs: list[RawJob] = []
        for card in tree.css("article.jobTuple, div.srp-jobtuple-wrapper"):
            title_el = card.css_first("a.title")
            if not title_el:
                continue
            url = (title_el.attributes.get("href") or "").split("?")[0]
            title = title_el.text(strip=True)
            if not title or not url:
                continue
            company_el = card.css_first("a.subTitle") or card.css_first("a.comp-name")
            loc_el = card.css_first("span.locWdth") or card.css_first("span.loc-wrap")
            jobs.append(
                RawJob(
                    source="naukri",
                    company_name=(company_el.text(strip=True) if company_el else "")
                    or (company_hint or "Unknown"),
                    title=title,
                    url=url,
                    location=loc_el.text(strip=True) if loc_el else None,
                )
            )
        return jobs
