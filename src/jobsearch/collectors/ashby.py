"""Ashby job board collector.

Public JSON API:
    https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true
"""

from __future__ import annotations

from collections.abc import Iterable

from jobsearch.collectors._util import parse_iso_date
from jobsearch.collectors.base import Collector
from jobsearch.models import RawJob
from jobsearch.registry.loader import CompanyTarget

API = "https://api.ashbyhq.com/posting-api/job-board/{token}"


class AshbyCollector(Collector):
    source = "ashby"

    @staticmethod
    def parse(payload: dict, company_name: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for item in payload.get("jobs", []) or []:
            # Only listed postings are publicly visible.
            if item.get("isListed") is False:
                continue
            jobs.append(
                RawJob(
                    source="ashby",
                    company_name=company_name,
                    title=(item.get("title") or "").strip(),
                    url=item.get("jobUrl") or item.get("applyUrl") or "",
                    source_job_id=item.get("id"),
                    location=item.get("location"),
                    employment_type=item.get("employmentType"),
                    description_html=item.get("descriptionHtml"),
                    description_text=item.get("descriptionPlain"),
                    created_date=parse_iso_date(item.get("publishedAt") or item.get("updatedAt")),
                    raw=item,
                )
            )
        return jobs

    def collect(self, company: CompanyTarget) -> Iterable[RawJob]:
        payload = self._http.get_json(
            API.format(token=company.token), params={"includeCompensation": "true"}
        )
        return self.parse(payload, company.name)
