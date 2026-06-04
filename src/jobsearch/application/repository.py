"""Persistence for application intelligence."""

from __future__ import annotations

from datetime import date

from jobsearch.application.config import ResumeSpec
from jobsearch.application.models import ApplicationRow, JobContext
from jobsearch.application.salary import Salary

_JOB_CONTEXT_COLS = """
    j.id, j.company_name, j.role_category, j.title, j.url, j.location,
    c.category, c.tier,
    s.match_score, s.priority, s.matched_skills, s.missing_skills,
    s.skill_score, s.experience_score, s.seniority_score, s.location_score, s.company_score,
    j.salary_min, j.salary_max, j.currency
"""


def _row_to_context(row) -> JobContext:
    return JobContext(
        job_id=row[0],
        company_name=row[1],
        role_category=row[2],
        title=row[3],
        url=row[4],
        location=row[5],
        company_category=row[6],
        company_tier=row[7],
        match_score=row[8],
        priority=row[9],
        matched_skills=list(row[10] or []),
        missing_skills=list(row[11] or []),
        skill_score=row[12],
        experience_score=row[13],
        seniority_score=row[14],
        location_score=row[15],
        company_score=row[16],
        salary_min=float(row[17]) if row[17] is not None else None,
        salary_max=float(row[18]) if row[18] is not None else None,
        currency=row[19],
    )


def fetch_job_context(conn, job_id: int) -> JobContext | None:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_JOB_CONTEXT_COLS} FROM jobs j "
            "LEFT JOIN companies c ON j.company_id = c.id "
            "LEFT JOIN job_scores s ON s.job_id = j.id WHERE j.id = %s",
            (job_id,),
        )
        row = cur.fetchone()
        return _row_to_context(row) if row else None


def list_high_priority(conn, limit: int | None = None) -> list[JobContext]:
    sql = (
        f"SELECT {_JOB_CONTEXT_COLS} FROM jobs j "
        "LEFT JOIN companies c ON j.company_id = c.id "
        "JOIN job_scores s ON s.job_id = j.id "
        "WHERE s.priority = 'HIGH' AND j.status = 'open' "
        "ORDER BY s.match_score DESC, j.id"
    )
    params: tuple = ()
    if limit:
        sql += " LIMIT %s"
        params = (limit,)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [_row_to_context(r) for r in cur.fetchall()]


# ---- salary ----------------------------------------------------------------

def jobs_missing_salary(conn) -> list[tuple[int, dict, str | None]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, raw, description FROM jobs "
            "WHERE salary_min IS NULL AND salary_max IS NULL"
        )
        return [(r[0], r[1] or {}, r[2]) for r in cur.fetchall()]


def update_salary(conn, job_id: int, salary: Salary) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET salary_min = %s, salary_max = %s, currency = %s, "
            "compensation_source = %s WHERE id = %s",
            (salary.salary_min, salary.salary_max, salary.currency, salary.source, job_id),
        )


# ---- company tiers ---------------------------------------------------------

def set_company_tier(conn, company_name: str, tier: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE companies SET tier = %s WHERE name = %s", (tier, company_name))


def all_company_names(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM companies")
        return [r[0] for r in cur.fetchall()]


# ---- resumes ---------------------------------------------------------------

def sync_resume(conn, spec: ResumeSpec) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO resumes (role_category, name, version, focus_skills, themes, file_path) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (role_category, name, version) DO UPDATE SET "
            "focus_skills = EXCLUDED.focus_skills, themes = EXCLUDED.themes, "
            "file_path = EXCLUDED.file_path RETURNING id",
            (spec.role_category, spec.name, spec.version, spec.focus_skills, spec.themes,
             spec.file_path),
        )
        return cur.fetchone()[0]


def resume_id_for(conn, role_category: str, name: str, version: int) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM resumes WHERE role_category = %s AND name = %s AND version = %s",
            (role_category, name, version),
        )
        row = cur.fetchone()
        return row[0] if row else None


# ---- recruiters ------------------------------------------------------------

def create_recruiter(conn, *, name, company=None, linkedin_url=None, email=None, notes=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO recruiters (name, company, linkedin_url, email, notes) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, company, linkedin_url, email, notes),
        )
        return cur.fetchone()[0]


def get_recruiter(conn, recruiter_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, company, linkedin_url, email, response_status, notes "
            "FROM recruiters WHERE id = %s",
            (recruiter_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = ["id", "name", "company", "linkedin_url", "email", "response_status", "notes"]
        return dict(zip(keys, row, strict=True))


def update_recruiter(conn, recruiter_id: int, *, response_status=None, notes=None,
                     mark_contacted=False) -> None:
    sets, params = [], []
    if response_status is not None:
        sets.append("response_status = %s")
        params.append(response_status)
    if notes is not None:
        sets.append("notes = %s")
        params.append(notes)
    if mark_contacted:
        sets.append("contacted_at = now()")
    if not sets:
        return
    params.append(recruiter_id)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE recruiters SET {', '.join(sets)} WHERE id = %s", params)


# ---- applications ----------------------------------------------------------

def create_application(conn, job_id: int, *, status="SAVED", notes=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO applications (job_id, status, notes) VALUES (%s, %s, %s) "
            "ON CONFLICT (job_id) DO UPDATE SET last_update = now() RETURNING id",
            (job_id, status, notes),
        )
        return cur.fetchone()[0]


def update_application(
    conn, job_id: int, *, status=None, recruiter_id=None, resume_id=None,
    resume_version=None, notes=None, application_date: date | None = None,
) -> bool:
    sets, params = ["last_update = now()"], []
    for col, val in [
        ("status", status),
        ("recruiter_id", recruiter_id),
        ("resume_id", resume_id),
        ("resume_version", resume_version),
        ("notes", notes),
        ("application_date", application_date),
    ]:
        if val is not None:
            sets.append(f"{col} = %s")
            params.append(val)
    params.append(job_id)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE applications SET {', '.join(sets)} WHERE job_id = %s", params)
        return cur.rowcount > 0


def list_applications(conn, *, status: str | None = None, limit: int | None = None
                      ) -> list[ApplicationRow]:
    sql = (
        "SELECT a.id, a.job_id, a.status, j.company_name, j.title, s.priority, s.match_score, "
        "a.application_date, a.last_update, a.recruiter_id, a.resume_id, a.notes "
        "FROM applications a JOIN jobs j ON j.id = a.job_id "
        "LEFT JOIN job_scores s ON s.job_id = j.id"
    )
    params: list = []
    if status:
        sql += " WHERE a.status = %s"
        params.append(status)
    sql += " ORDER BY a.last_update DESC"
    if limit:
        sql += " LIMIT %s"
        params.append(limit)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        ApplicationRow(
            id=r[0], job_id=r[1], status=r[2], company_name=r[3], title=r[4],
            priority=r[5], match_score=r[6], application_date=r[7],
            last_update=str(r[8]) if r[8] else None,
            recruiter_id=r[9], resume_id=r[10], notes=r[11],
        )
        for r in rows
    ]


# ---- artifacts (deduped) ---------------------------------------------------

def get_artifact(conn, job_id: int, kind: str, input_hash: str) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content FROM application_artifacts "
            "WHERE job_id = %s AND kind = %s AND input_hash = %s",
            (job_id, kind, input_hash),
        )
        row = cur.fetchone()
        return row[0] if row else None


def store_artifact(conn, job_id: int, kind: str, content: str, generated_by: str,
                   input_hash: str) -> tuple[str, str]:
    """Insert an artifact, or return the existing one. Returns (status, content)
    where status is 'created' or 'exists'."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO application_artifacts (job_id, kind, content, generated_by, input_hash) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (job_id, kind, input_hash) DO NOTHING RETURNING id",
            (job_id, kind, content, generated_by, input_hash),
        )
        inserted = cur.fetchone() is not None
    if inserted:
        return "created", content
    return "exists", get_artifact(conn, job_id, kind, input_hash) or content


# ---- generation token ledger ----------------------------------------------

def generation_tokens_today(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) "
            "FROM generation_runs WHERE started_at::date = CURRENT_DATE"
        )
        return int(cur.fetchone()[0])


def record_generation(conn, kind: str, input_tokens: int, output_tokens: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO generation_runs (kind, input_tokens, output_tokens) VALUES (%s, %s, %s)",
            (kind, input_tokens, output_tokens),
        )
