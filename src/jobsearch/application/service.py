"""Application-intelligence orchestration: gating, generation, dedup, tracking."""

from __future__ import annotations

import os
from dataclasses import dataclass

from jobsearch.application import generate, llm
from jobsearch.application import repository as repo
from jobsearch.application.config import ApplicationConfig, Candidate, CompanyTiers
from jobsearch.application.models import (
    KIND_COVER_LETTER,
    KIND_RECOMMENDATION,
    JobContext,
    Recommendation,
)
from jobsearch.application.recommend import build_recommendation
from jobsearch.application.resumes import ResumeLibrary
from jobsearch.config import Settings
from jobsearch.db.connection import connect
from jobsearch.logging_config import get_logger

log = get_logger("application")

DETERMINISTIC = "deterministic"


@dataclass
class GenResult:
    kind: str
    status: str            # created / exists / skipped
    generated_by: str | None = None
    content: str | None = None
    reason: str | None = None


class ApplicationService:
    def __init__(
        self,
        settings: Settings,
        config: ApplicationConfig | None = None,
        candidate: Candidate | None = None,
        library: ResumeLibrary | None = None,
        tiers: CompanyTiers | None = None,
    ):
        self._settings = settings
        self._config = config or ApplicationConfig.from_config()
        self._candidate = candidate or Candidate.from_config()
        self._library = library or ResumeLibrary.from_config()
        self._tiers = tiers or CompanyTiers.from_config()

    # ---- context helpers --------------------------------------------------

    def _context(self, conn, job_id: int) -> JobContext | None:
        job = repo.fetch_job_context(conn, job_id)
        if job and not job.company_tier:
            job.company_tier = self._tiers.tier_for(job.company_name)
        return job

    def _cover_letter_allowed(self, job: JobContext, force: bool) -> tuple[bool, str]:
        if force:
            return True, "forced"
        if (job.priority or "") != self._config.cover_letter_require_priority:
            return False, (
                f"priority {job.priority} != {self._config.cover_letter_require_priority}"
            )
        if (job.match_score or 0) < self._config.cover_letter_min_score:
            return False, f"score {job.match_score} < {self._config.cover_letter_min_score}"
        return True, "passes gate"

    def _llm_enabled(self, conn, use_llm: bool | None) -> bool:
        want = self._config.use_llm if use_llm is None else use_llm
        if not want:
            return False
        if not os.getenv("ANTHROPIC_API_KEY"):
            log.warning("llm_skipped", reason="ANTHROPIC_API_KEY not set")
            return False
        if repo.generation_tokens_today(conn) >= self._config.max_tokens_per_day:
            log.warning("llm_skipped", reason="daily token budget exhausted")
            return False
        return True

    def _produce(self, conn, job: JobContext, kind: str, draft: str, input_hash: str,
                 use_llm: bool) -> GenResult:
        existing = repo.get_artifact(conn, job.job_id, kind, input_hash)
        if existing is not None:
            return GenResult(kind=kind, status="exists", content=existing)

        generated_by = DETERMINISTIC
        content = draft
        if use_llm:
            try:
                content, usage = llm.polish(kind, job, draft, self._candidate, self._config)
                repo.record_generation(conn, kind, usage.input_tokens, usage.output_tokens)
                generated_by = self._config.model
            except Exception as exc:  # noqa: BLE001 — fall back to the deterministic draft
                log.warning("llm_polish_failed", kind=kind, error=str(exc))

        status, stored = repo.store_artifact(conn, job.job_id, kind, content, generated_by,
                                             input_hash)
        return GenResult(kind=kind, status=status, generated_by=generated_by, content=stored)

    # ---- resume + recommendation -----------------------------------------

    def select_resume(self, job_id: int) -> dict:
        with connect(self._settings.database_url) as conn:
            job = self._context(conn, job_id)
            if not job:
                raise ValueError(f"job {job_id} not found")
            resume, reason = self._library.select_best(job)
            recs = self._library.recommendations(resume, job)
        return {"resume": resume, "reason": reason, "recommendations": recs, "job": job}

    def recommend(self, job_id: int, *, store: bool = True) -> tuple[Recommendation, JobContext]:
        with connect(self._settings.database_url) as conn:
            job = self._context(conn, job_id)
            if not job:
                raise ValueError(f"job {job_id} not found")
            rec = build_recommendation(job, self._library, self._config)
            if store:
                content = rec.to_text(job)
                ihash = generate.artifact_input_hash(KIND_RECOMMENDATION, job, resume=rec.resume)
                repo.store_artifact(
                    conn, job_id, KIND_RECOMMENDATION, content, DETERMINISTIC, ihash
                )
        return rec, job

    def recommend_high_priority(self, limit: int | None = None) -> list[tuple[Recommendation,
                                                                              JobContext]]:
        """Deterministic recommendations for HIGH-priority jobs only (0 tokens)."""
        out = []
        with connect(self._settings.database_url) as conn:
            jobs = repo.list_high_priority(conn, limit)
            for job in jobs:
                if not job.company_tier:
                    job.company_tier = self._tiers.tier_for(job.company_name)
                rec = build_recommendation(job, self._library, self._config)
                content = rec.to_text(job)
                ihash = generate.artifact_input_hash(KIND_RECOMMENDATION, job, resume=rec.resume)
                repo.store_artifact(conn, job.job_id, KIND_RECOMMENDATION, content, DETERMINISTIC,
                                    ihash)
                out.append((rec, job))
        return out

    # ---- generation -------------------------------------------------------

    def generate_cover_letter(self, job_id: int, *, force: bool = False,
                              use_llm: bool | None = None) -> GenResult:
        with connect(self._settings.database_url) as conn:
            job = self._context(conn, job_id)
            if not job:
                raise ValueError(f"job {job_id} not found")
            allowed, reason = self._cover_letter_allowed(job, force)
            if not allowed:
                return GenResult(kind=KIND_COVER_LETTER, status="skipped", reason=reason)
            resume, _ = self._library.select_best(job)
            draft = generate.cover_letter(self._candidate, job, resume)
            ihash = generate.artifact_input_hash(KIND_COVER_LETTER, job, resume=resume)
            return self._produce(conn, job, KIND_COVER_LETTER, draft, ihash,
                                  self._llm_enabled(conn, use_llm))

    def generate_outreach(self, job_id: int, *, kinds: list[str], recruiter_id: int | None = None,
                          use_llm: bool | None = None) -> list[GenResult]:
        results: list[GenResult] = []
        with connect(self._settings.database_url) as conn:
            job = self._context(conn, job_id)
            if not job:
                raise ValueError(f"job {job_id} not found")
            recruiter_name = None
            if recruiter_id is not None:
                rec = repo.get_recruiter(conn, recruiter_id)
                recruiter_name = rec["name"] if rec else None
            llm_on = self._llm_enabled(conn, use_llm)
            resume, _ = self._library.select_best(job)
            for kind in kinds:
                gen = generate.GENERATORS.get(kind)
                if not gen:
                    continue
                draft = gen(self._candidate, job, resume, recruiter_name)
                ihash = generate.artifact_input_hash(kind, job, resume=resume,
                                                     recruiter_name=recruiter_name)
                results.append(self._produce(conn, job, kind, draft, ihash, llm_on))
        return results

    # ---- tracking ---------------------------------------------------------

    def create_application(self, job_id: int, *, status: str = "SAVED", notes=None) -> int:
        with connect(self._settings.database_url) as conn:
            if not repo.fetch_job_context(conn, job_id):
                raise ValueError(f"job {job_id} not found")
            return repo.create_application(conn, job_id, status=status, notes=notes)

    def update_application(self, job_id: int, **kwargs) -> bool:
        with connect(self._settings.database_url) as conn:
            return repo.update_application(conn, job_id, **kwargs)

    def list_applications(self, *, status=None, limit=None):
        with connect(self._settings.database_url) as conn:
            return repo.list_applications(conn, status=status, limit=limit)

    # ---- recruiters -------------------------------------------------------

    def add_recruiter(self, **kwargs) -> int:
        with connect(self._settings.database_url) as conn:
            return repo.create_recruiter(conn, **kwargs)

    # ---- maintenance ------------------------------------------------------

    def backfill_salary(self) -> int:
        from jobsearch.application.salary import extract_salary

        updated = 0
        with connect(self._settings.database_url) as conn:
            for job_id, raw, description in repo.jobs_missing_salary(conn):
                salary = extract_salary(raw, description)
                if salary.found:
                    repo.update_salary(conn, job_id, salary)
                    updated += 1
        return updated

    def sync_tiers(self) -> int:
        with connect(self._settings.database_url) as conn:
            names = repo.all_company_names(conn)
            for name in names:
                repo.set_company_tier(conn, name, self._tiers.tier_for(name))
        return len(names)

    def sync_resumes(self) -> int:
        with connect(self._settings.database_url) as conn:
            for spec in self._library.resumes:
                repo.sync_resume(conn, spec)
        return len(self._library.resumes)
