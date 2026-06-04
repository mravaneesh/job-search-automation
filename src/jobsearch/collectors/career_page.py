"""Generic, config-driven company career-page collector.

Many company career sites expose a structured JSON search endpoint. Rather than
writing bespoke code per company, this collector is driven entirely by the
``spec`` block in the registry, e.g.::

    spec:
      url: "https://www.amazon.jobs/en/search.json"
      params: { base_query: "software engineer", result_limit: 100 }
      results_path: "jobs"
      pagination: { offset_param: "offset", page_size: 100, max_pages: 3 }
      url_prefix: "https://www.amazon.jobs"
      fields:
        source_job_id: "id_icims"
        title: "title"
        url: "job_path"
        location: "normalized_location"
        description_html: "description"
        created_date: "posted_date"
        employment_type: "job_schedule_type"

Only companies with a stable JSON endpoint should use this. There is no HTML
scraping and no LLM — purely field mapping over JSON.
"""

from __future__ import annotations

from collections.abc import Iterable

from jobsearch.collectors._util import get_path, parse_loose_date
from jobsearch.collectors.base import Collector
from jobsearch.models import RawJob
from jobsearch.registry.loader import CompanyTarget

_DATE_FIELDS = {"created_date"}


class CareerPageCollector(Collector):
    source = "career_page"

    @staticmethod
    def parse(items: list, company_name: str, spec: dict) -> list[RawJob]:
        fields = spec.get("fields", {})
        url_prefix = spec.get("url_prefix", "")
        jobs: list[RawJob] = []
        for item in items or []:
            mapped: dict = {}
            for target, path in fields.items():
                value = get_path(item, path) if isinstance(item, dict) else None
                if target in _DATE_FIELDS:
                    mapped[target] = parse_loose_date(value)
                else:
                    mapped[target] = value

            url = mapped.get("url") or ""
            if url and url_prefix and url.startswith("/"):
                url = url_prefix.rstrip("/") + url

            title = (mapped.get("title") or "").strip()
            if not title or not url:
                continue

            jobs.append(
                RawJob(
                    source="career_page",
                    company_name=company_name,
                    title=title,
                    url=url,
                    source_job_id=(
                        str(mapped["source_job_id"])
                        if mapped.get("source_job_id") is not None
                        else None
                    ),
                    location=mapped.get("location"),
                    employment_type=mapped.get("employment_type"),
                    description_html=mapped.get("description_html"),
                    description_text=mapped.get("description_text"),
                    created_date=mapped.get("created_date"),
                    raw=item,
                )
            )
        return jobs

    def collect(self, company: CompanyTarget) -> Iterable[RawJob]:
        spec = company.spec
        if not spec or not spec.get("url"):
            return []
        results_path = spec.get("results_path", "")
        base_params = dict(spec.get("params", {}))
        pagination = spec.get("pagination") or {}

        all_jobs: list[RawJob] = []
        if pagination:
            offset_param = pagination["offset_param"]
            page_size = int(pagination.get("page_size", 100))
            max_pages = int(pagination.get("max_pages", 1))
            for page in range(max_pages):
                params = dict(base_params)
                params[offset_param] = page * page_size
                payload = self._http.get_json(spec["url"], params=params)
                items = get_path(payload, results_path) if results_path else payload
                page_jobs = self.parse(items or [], company.name, spec)
                all_jobs.extend(page_jobs)
                if len(page_jobs) < page_size:
                    break
        else:
            payload = self._http.get_json(spec["url"], params=base_params)
            items = get_path(payload, results_path) if results_path else payload
            all_jobs.extend(self.parse(items or [], company.name, spec))
        return all_jobs
