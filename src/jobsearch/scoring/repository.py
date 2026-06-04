"""Persistence for scoring: read candidate jobs, write scores, track tokens."""

from __future__ import annotations

from jobsearch.scoring.models import JobInput, ScoreResult

# Open jobs joined with their company category and any existing score state.
_SELECT_JOBS = """
SELECT j.id, j.company_name, j.role_category, j.title, j.location, j.experience,
       j.employment_type, j.skills, c.category,
       s.input_hash, s.scorer_version
FROM jobs j
LEFT JOIN companies c  ON j.company_id = c.id
LEFT JOIN job_scores s ON s.job_id = j.id
WHERE j.status = 'open'
ORDER BY j.id
"""

_UPSERT_SCORE = """
INSERT INTO job_scores (
    job_id, role_category, match_score, skill_score, experience_score,
    location_score, seniority_score, company_score, interview_likelihood,
    matched_skills, missing_skills, priority, scorer_version, scored_by, input_hash
) VALUES (
    %(job_id)s, %(role_category)s, %(match_score)s, %(skill_score)s,
    %(experience_score)s, %(location_score)s, %(seniority_score)s,
    %(company_score)s, %(interview_likelihood)s, %(matched_skills)s,
    %(missing_skills)s, %(priority)s, %(scorer_version)s, %(scored_by)s,
    %(input_hash)s
)
ON CONFLICT (job_id) DO UPDATE SET
    role_category        = EXCLUDED.role_category,
    match_score          = EXCLUDED.match_score,
    skill_score          = EXCLUDED.skill_score,
    experience_score     = EXCLUDED.experience_score,
    location_score       = EXCLUDED.location_score,
    seniority_score      = EXCLUDED.seniority_score,
    company_score        = EXCLUDED.company_score,
    interview_likelihood = EXCLUDED.interview_likelihood,
    matched_skills       = EXCLUDED.matched_skills,
    missing_skills       = EXCLUDED.missing_skills,
    priority             = EXCLUDED.priority,
    scorer_version       = EXCLUDED.scorer_version,
    scored_by            = EXCLUDED.scored_by,
    input_hash           = EXCLUDED.input_hash,
    updated_at           = now();
"""


class CandidateRow:
    """A job row plus its existing score state (if any)."""

    def __init__(self, row):
        (
            self.job_id,
            self.company_name,
            self.role_category,
            self.title,
            self.location,
            self.experience,
            self.employment_type,
            self.skills,
            self.company_category,
            self.input_hash,
            self.scorer_version,
        ) = row

    def to_input(self) -> JobInput:
        return JobInput(
            job_id=self.job_id,
            company_name=self.company_name,
            role_category=self.role_category,
            title=self.title,
            location=self.location,
            experience=self.experience,
            employment_type=self.employment_type,
            skills=list(self.skills or []),
            company_category=self.company_category,
        )


def select_candidates(conn) -> list[CandidateRow]:
    with conn.cursor() as cur:
        cur.execute(_SELECT_JOBS)
        return [CandidateRow(r) for r in cur.fetchall()]


def upsert_score(conn, result: ScoreResult, scorer_version: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            _UPSERT_SCORE,
            {
                "job_id": result.job_id,
                "role_category": result.role_category,
                "match_score": result.match_score,
                "skill_score": result.skill_score,
                "experience_score": result.experience_score,
                "location_score": result.location_score,
                "seniority_score": result.seniority_score,
                "company_score": result.company_score,
                "interview_likelihood": result.interview_likelihood,
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills,
                "priority": result.priority,
                "scorer_version": scorer_version,
                "scored_by": result.scored_by,
                "input_hash": result.input_hash,
            },
        )


def tokens_used_today(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) "
            "FROM scoring_runs WHERE started_at::date = CURRENT_DATE"
        )
        return int(cur.fetchone()[0])


def start_run(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO scoring_runs (status) VALUES ('running') RETURNING id"
        )
        return cur.fetchone()[0]


def finish_run(
    conn,
    run_id: int,
    *,
    considered: int,
    scored: int,
    llm_calls: int,
    input_tokens: int,
    output_tokens: int,
    status: str,
    error: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE scoring_runs SET finished_at = now(), jobs_considered = %s, "
            "jobs_scored = %s, llm_calls = %s, input_tokens = %s, "
            "output_tokens = %s, status = %s, error = %s WHERE id = %s",
            (considered, scored, llm_calls, input_tokens, output_tokens, status, error, run_id),
        )
