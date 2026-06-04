"""Orchestration: registry -> collectors -> normalize -> dedup -> storage."""

from __future__ import annotations

from dataclasses import dataclass, field

from jobsearch.collectors.aggregator_base import ROLE_QUERIES
from jobsearch.collectors.registry import AGGREGATOR_COLLECTORS, COMPANY_COLLECTORS
from jobsearch.config import Settings
from jobsearch.db import repository as repo
from jobsearch.db.connection import connect
from jobsearch.http import HttpClient
from jobsearch.logging_config import get_logger
from jobsearch.models import Job, RawJob
from jobsearch.normalize.normalizer import Normalizer
from jobsearch.registry.loader import Registry, load_registry

log = get_logger("pipeline")


@dataclass
class TargetResult:
    label: str
    source: str
    found: int = 0
    matched: int = 0
    inserted: int = 0
    updated: int = 0
    status: str = "success"
    error: str | None = None


@dataclass
class RunSummary:
    results: list[TargetResult] = field(default_factory=list)

    @property
    def totals(self) -> dict[str, int]:
        return {
            "targets": len(self.results),
            "found": sum(r.found for r in self.results),
            "matched": sum(r.matched for r in self.results),
            "inserted": sum(r.inserted for r in self.results),
            "updated": sum(r.updated for r in self.results),
            "failed": sum(1 for r in self.results if r.status == "failed"),
        }


class Pipeline:
    def __init__(self, settings: Settings, registry: Registry | None = None):
        self._settings = settings
        self._registry = registry or load_registry()
        self._normalizer = Normalizer.default()

    def run(
        self,
        *,
        sources: set[str] | None = None,
        companies: set[str] | None = None,
        dry_run: bool = False,
        limit: int | None = None,
    ) -> RunSummary:
        summary = RunSummary()
        with HttpClient(self._settings) as http:
            for company in self._registry.companies:
                if not company.is_implemented:
                    continue
                if sources and company.source not in sources:
                    continue
                if companies and company.name not in companies:
                    continue
                summary.results.append(self._run_company(http, company, dry_run, limit))

        for agg in self._registry.aggregators:
            if not agg.is_implemented:
                continue
            if sources and agg.source not in sources:
                continue
            summary.results.append(self._run_aggregator(agg, dry_run, limit))

        log.info("collection_complete", **summary.totals)
        return summary

    # -- company (API / career-page) targets -------------------------------

    def _run_company(self, http, company, dry_run, limit) -> TargetResult:
        result = TargetResult(label=company.name, source=company.source)
        collector = COMPANY_COLLECTORS[company.source](http)
        try:
            raw = list(collector.collect(company))
        except Exception as exc:  # noqa: BLE001 — collectors are best-effort
            log.warning(
                "collect_failed", company=company.name, source=company.source, error=str(exc)
            )
            result.status = "failed"
            result.error = str(exc)
            return result

        if limit:
            raw = raw[:limit]
        self._persist(result, raw, dry_run, company_target=company)
        log.info(
            "company_done",
            company=company.name,
            source=company.source,
            found=result.found,
            matched=result.matched,
            inserted=result.inserted,
            updated=result.updated,
        )
        return result

    # -- aggregator (Playwright) targets ------------------------------------

    def _run_aggregator(self, agg, dry_run, limit) -> TargetResult:
        result = TargetResult(label=agg.source, source=agg.source)
        collector = AGGREGATOR_COLLECTORS[agg.source](self._settings)
        raw: list[RawJob] = []
        try:
            for _role, query in ROLE_QUERIES.items():
                for location in agg.locations or ["Remote"]:
                    raw.extend(collector.search(query, location))
        except Exception as exc:  # noqa: BLE001
            log.warning("aggregator_failed", source=agg.source, error=str(exc))
            result.status = "failed"
            result.error = str(exc)
            return result

        if limit:
            raw = raw[:limit]
        self._persist(result, raw, dry_run, company_target=None)
        return result

    # -- shared normalize + persist -----------------------------------------

    def _persist(self, result: TargetResult, raw: list[RawJob], dry_run: bool, company_target):
        result.found = len(raw)
        jobs: list[Job] = []
        for r in raw:
            job = self._normalizer.normalize(r)
            if job is not None:
                jobs.append(job)
        result.matched = len(jobs)

        if dry_run or not jobs:
            return

        with connect(self._settings.database_url) as conn:
            company_id = repo.upsert_company(conn, company_target) if company_target else None
            company_label = company_target.name if company_target else None
            run_id = repo.start_run(conn, result.source, company_label)
            for job in jobs:
                outcome = repo.upsert_job(conn, job, company_id)
                if outcome == "inserted":
                    result.inserted += 1
                else:
                    result.updated += 1
            repo.finish_run(
                conn,
                run_id,
                found=result.found,
                inserted=result.inserted,
                updated=result.updated,
                status="success",
            )


def renormalize(settings: Settings) -> int:
    """Re-run normalization over stored raw payloads (no re-fetch).

    Returns the number of jobs updated. Useful after tuning roles/skills.
    """
    from jobsearch.collectors.greenhouse import GreenhouseCollector  # noqa: F401

    normalizer = Normalizer.default()
    updated = 0
    with connect(settings.database_url) as conn:
        rows = list(repo.fetch_raw_jobs(conn))
        for job_id, company_name, source, raw in rows:
            raw_job = RawJob(
                source=source,
                company_name=company_name,
                title=str(raw.get("title") or raw.get("text") or ""),
                url="",
                description_html=raw.get("content") or raw.get("description") or raw.get(
                    "descriptionHtml"
                ),
                description_text=raw.get("descriptionPlain"),
                raw=raw,
            )
            job = normalizer.normalize(raw_job)
            if job is None:
                continue
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET role_category = %s, skills = %s, experience = %s "
                    "WHERE id = %s",
                    (job.role_category, job.skills, job.experience, job_id),
                )
            updated += 1
    return updated
