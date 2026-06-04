"""Lever postings collector.

Public JSON API:
    https://api.lever.co/v0/postings/{token}?mode=json
"""

from __future__ import annotations

from collections.abc import Iterable

from jobsearch.collectors._util import parse_epoch_ms
from jobsearch.collectors.base import Collector
from jobsearch.models import RawJob
from jobsearch.registry.loader import CompanyTarget

API = "https://api.lever.co/v0/postings/{token}"


class LeverCollector(Collector):
    source = "lever"

    @staticmethod
    def parse(payload: list, company_name: str) -> list[RawJob]:
        jobs: list[RawJob] = []
        for item in payload or []:
            categories = item.get("categories") or {}
            jobs.append(
                RawJob(
                    source="lever",
                    company_name=company_name,
                    title=(item.get("text") or "").strip(),
                    url=item.get("hostedUrl") or item.get("applyUrl") or "",
                    source_job_id=item.get("id"),
                    location=categories.get("location"),
                    employment_type=categories.get("commitment"),
                    description_html=item.get("description"),
                    description_text=item.get("descriptionPlain"),
                    created_date=parse_epoch_ms(item.get("createdAt")),
                    raw=item,
                )
            )
        return jobs

    def collect(self, company: CompanyTarget) -> Iterable[RawJob]:
        payload = self._http.get_json(API.format(token=company.token), params={"mode": "json"})
        return self.parse(payload, company.name)
