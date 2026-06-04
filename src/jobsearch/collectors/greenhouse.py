"""Greenhouse job board collector.

Public JSON API:
    https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
"""

from __future__ import annotations

from collections.abc import Iterable

from jobsearch.collectors._util import parse_iso_date
from jobsearch.collectors.base import Collector
from jobsearch.models import RawJob
from jobsearch.registry.loader import CompanyTarget

API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


class GreenhouseCollector(Collector):
    source = "greenhouse"

    @staticmethod
    def parse(payload: dict, company_name: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for item in payload.get("jobs", []) or []:
            location = (item.get("location") or {}).get("name")
            created = parse_iso_date(item.get("first_published") or item.get("updated_at"))
            jobs.append(
                RawJob(
                    source="greenhouse",
                    company_name=company_name,
                    title=(item.get("title") or "").strip(),
                    url=item.get("absolute_url") or "",
                    source_job_id=str(item["id"]) if item.get("id") is not None else None,
                    location=location,
                    description_html=item.get("content"),
                    created_date=created,
                    raw=item,
                )
            )
        return jobs

    def collect(self, company: CompanyTarget) -> Iterable[RawJob]:
        payload = self._http.get_json(API.format(token=company.token), params={"content": "true"})
        return self.parse(payload, company.name)
