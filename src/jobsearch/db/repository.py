"""Persistence: companies, jobs (idempotent upsert), collection runs."""

from __future__ import annotations

from psycopg.types.json import Json

from jobsearch.models import Job
from jobsearch.registry.loader import CompanyTarget

_UPSERT_COMPANY = """
INSERT INTO companies (name, category, primary_source, source_token, status)
VALUES (%(name)s, %(category)s, %(source)s, %(token)s, %(status)s)
ON CONFLICT (name) DO UPDATE SET
    category       = EXCLUDED.category,
    primary_source = EXCLUDED.primary_source,
    source_token   = EXCLUDED.source_token,
    status         = EXCLUDED.status
RETURNING id;
"""

# Insert a job, or on fingerprint conflict refresh last_seen_at and re-open it.
# Canonical fields are overwritten only when the incoming source has equal or
# higher priority (lower source_priority value) than the stored row, so a
# career-page listing wins over the same role found on an ATS.
_UPSERT_JOB = """
INSERT INTO jobs (
    company_id, company_name, role_category, title, source, source_priority,
    source_job_id, url, location, experience, employment_type, description,
    skills, created_date, fingerprint, raw
) VALUES (
    %(company_id)s, %(company_name)s, %(role_category)s, %(title)s, %(source)s,
    %(source_priority)s, %(source_job_id)s, %(url)s, %(location)s, %(experience)s,
    %(employment_type)s, %(description)s, %(skills)s, %(created_date)s,
    %(fingerprint)s, %(raw)s
)
ON CONFLICT (fingerprint) DO UPDATE SET
    last_seen_at    = now(),
    status          = 'open',
    company_id      = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.company_id ELSE jobs.company_id END,
    role_category   = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.role_category ELSE jobs.role_category END,
    title           = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.title ELSE jobs.title END,
    source          = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.source ELSE jobs.source END,
    source_priority = LEAST(EXCLUDED.source_priority, jobs.source_priority),
    source_job_id   = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.source_job_id ELSE jobs.source_job_id END,
    url             = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.url ELSE jobs.url END,
    location        = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.location ELSE jobs.location END,
    experience      = COALESCE(EXCLUDED.experience, jobs.experience),
    employment_type = COALESCE(EXCLUDED.employment_type, jobs.employment_type),
    description     = COALESCE(EXCLUDED.description, jobs.description),
    skills          = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.skills ELSE jobs.skills END,
    created_date    = COALESCE(jobs.created_date, EXCLUDED.created_date),
    raw             = CASE WHEN EXCLUDED.source_priority <= jobs.source_priority
                           THEN EXCLUDED.raw ELSE jobs.raw END
RETURNING (xmax = 0) AS inserted;
"""


def upsert_company(conn, target: CompanyTarget) -> int:
    with conn.cursor() as cur:
        cur.execute(
            _UPSERT_COMPANY,
            {
                "name": target.name,
                "category": target.category,
                "source": target.source,
                "token": target.token,
                "status": target.status,
            },
        )
        return cur.fetchone()[0]


def upsert_job(conn, job: Job, company_id: int | None) -> str:
    """Insert or update a job. Returns 'inserted' or 'updated'."""
    with conn.cursor() as cur:
        cur.execute(
            _UPSERT_JOB,
            {
                "company_id": company_id,
                "company_name": job.company_name,
                "role_category": job.role_category,
                "title": job.title,
                "source": job.source,
                "source_priority": job.source_priority,
                "source_job_id": job.source_job_id,
                "url": job.url,
                "location": job.location,
                "experience": job.experience,
                "employment_type": job.employment_type,
                "description": job.description,
                "skills": job.skills,
                "created_date": job.created_date,
                "fingerprint": job.fingerprint,
                "raw": Json(job.raw) if job.raw else None,
            },
        )
        inserted = cur.fetchone()[0]
    return "inserted" if inserted else "updated"


def start_run(conn, source: str, company_name: str | None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO collection_runs (source, company_name, status) "
            "VALUES (%s, %s, 'running') RETURNING id",
            (source, company_name),
        )
        return cur.fetchone()[0]


def finish_run(
    conn,
    run_id: int,
    *,
    found: int,
    inserted: int,
    updated: int,
    status: str,
    error: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE collection_runs SET finished_at = now(), jobs_found = %s, "
            "jobs_inserted = %s, jobs_updated = %s, status = %s, error = %s WHERE id = %s",
            (found, inserted, updated, status, error, run_id),
        )


def fetch_raw_jobs(conn):
    """Yield (id, company_name, source, raw) for re-normalization."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, company_name, source, raw FROM jobs WHERE raw IS NOT NULL")
        yield from cur.fetchall()
