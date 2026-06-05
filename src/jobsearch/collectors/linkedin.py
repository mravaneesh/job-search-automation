"""LinkedIn aggregator collector (Playwright + httpx, best-effort).

Search uses the public guest jobs endpoint (Playwright). Each result is then
enriched with its full description via the public guest *job-detail* endpoint
(plain httpx, no browser) so experience parsing, skill extraction, and seniority
filtering work on LinkedIn jobs too. Enrichment is cached per run and fails
soft: a job that can't be enriched simply keeps its card-level fields.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import httpx
from selectolax.parser import HTMLParser

from jobsearch.collectors.aggregator_base import AggregatorCollector
from jobsearch.config import Settings
from jobsearch.models import RawJob

# The guest endpoint returns ~10 cards per call; page through a few of them.
_PAGE_SIZE = 10
_MAX_PAGES = 5

_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
_ENRICH_WORKERS = 4  # higher concurrency trips LinkedIn's rate limit (429)
_JOB_ID = re.compile(r"(\d{6,})")


class LinkedInCollector(AggregatorCollector):
    source = "linkedin"

    def __init__(self, settings: Settings):
        super().__init__(settings)
        # jobId -> (description_html, employment_type); dedupes across searches.
        self._detail_cache: dict[str, tuple[str | None, str | None]] = {}

    def build_url(self, query: str, location: str, start: int = 0) -> str:
        return (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote_plus(query)}&location={quote_plus(location)}&start={start}"
        )

    def search(self, query: str, location: str) -> Iterable[RawJob]:
        """Page through the guest endpoint, then enrich with descriptions."""
        urls = [
            self.build_url(query, location, start=i * _PAGE_SIZE) for i in range(_MAX_PAGES)
        ]
        jobs: list[RawJob] = []
        seen: set[str] = set()
        for html in self._iter_html(urls):
            page_jobs = self.parse(html)
            if not page_jobs:
                break  # no more results — stop fetching further pages
            for job in page_jobs:
                if job.url in seen:
                    continue
                seen.add(job.url)
                jobs.append(job)

        self._enrich(jobs)
        return jobs

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
            urn = card.attributes.get("data-entity-urn") or ""
            m = _JOB_ID.search(urn) or _JOB_ID.search(url)
            company_el = card.css_first(".base-search-card__subtitle")
            location_el = card.css_first(".job-search-card__location")
            jobs.append(
                RawJob(
                    source="linkedin",
                    company_name=(company_el.text(strip=True) if company_el else "")
                    or (company_hint or "Unknown"),
                    title=title,
                    url=url,
                    source_job_id=m.group(1) if m else None,
                    location=location_el.text(strip=True) if location_el else None,
                )
            )
        return jobs

    # ---- description enrichment (httpx, no browser) -----------------------

    def _enrich(self, jobs: list[RawJob]) -> None:
        todo = [
            j.source_job_id
            for j in jobs
            if j.source_job_id and j.source_job_id not in self._detail_cache
        ]
        if todo:
            ua = self._settings.http_user_agent
            with ThreadPoolExecutor(max_workers=_ENRICH_WORKERS) as ex:
                for job_id, data in zip(
                    todo,
                    ex.map(lambda jid: self._fetch_detail(jid, ua), todo),
                    strict=False,
                ):
                    self._detail_cache[job_id] = data

        for job in jobs:
            data = self._detail_cache.get(job.source_job_id or "")
            if not data:
                continue
            desc_html, emp_type = data
            if desc_html:
                job.description_html = desc_html
            if emp_type and not job.employment_type:
                job.employment_type = emp_type

    @staticmethod
    def _fetch_detail(job_id: str, user_agent: str) -> tuple[str | None, str | None]:
        url = _DETAIL_URL.format(job_id=job_id)
        headers = {"User-Agent": user_agent}
        for attempt in range(2):  # one retry on rate-limit
            try:
                r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
                if r.status_code == 429 and attempt == 0:
                    time.sleep(1.5)
                    continue
                if r.status_code != 200:
                    return (None, None)
                return LinkedInCollector._parse_detail(r.text)
            except Exception:  # noqa: BLE001 — best-effort; keep the card as-is
                return (None, None)
        return (None, None)

    @staticmethod
    def _parse_detail(html: str) -> tuple[str | None, str | None]:
        tree = HTMLParser(html or "")
        desc = tree.css_first(".show-more-less-html__markup") or tree.css_first(
            ".description__text"
        )
        desc_html = desc.html if desc else None
        # Criteria list is typically [seniority, employment type, function, ...].
        criteria = [c.text(strip=True) for c in tree.css(".description__job-criteria-text")]
        employment_type = criteria[1] if len(criteria) > 1 else None
        return (desc_html, employment_type)
