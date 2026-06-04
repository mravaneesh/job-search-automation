"""End-to-end scoring against a live PostgreSQL database.

Skipped unless DATABASE_URL is set. Verifies that scoring persists, that
unchanged jobs are not re-scored, and that changed inputs are picked up.
"""

from __future__ import annotations

import os
import uuid

import pytest

from jobsearch.config import load_settings
from jobsearch.db.connection import connect
from jobsearch.db.migrate import run_migrations
from jobsearch.scoring.service import ScoringService

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    run_migrations(DATABASE_URL)


def _insert_job(conn, *, title, skills, category="global", fingerprint=None):
    fingerprint = fingerprint or uuid.uuid4().hex
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO companies (name, category, status) VALUES (%s, %s, 'implemented') "
            "ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category RETURNING id",
            (f"Co-{fingerprint[:8]}", category),
        )
        company_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO jobs (company_id, company_name, role_category, title, source, url, "
            "location, experience, skills, fingerprint) VALUES "
            "(%s, %s, 'android', %s, 'greenhouse', %s, 'Remote', '2+ years', %s, %s) RETURNING id",
            (company_id, "Acme", title, f"https://x/{fingerprint}", skills, fingerprint),
        )
        return cur.fetchone()[0], fingerprint


def test_scores_persist_and_unchanged_jobs_are_skipped():
    settings = load_settings()
    with connect(DATABASE_URL) as conn:
        job_id, fp = _insert_job(conn, title="Android Engineer", skills=["Kotlin", "Android SDK"])

    # First run scores it.
    summary = ScoringService(settings).run(use_llm=False)
    assert summary.scored >= 1

    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT match_score, priority FROM job_scores WHERE job_id = %s", (job_id,))
        match_score, priority = cur.fetchone()
        assert match_score >= 75
        assert priority == "HIGH"

    # Second run: the job is unchanged, so it is not reconsidered.
    ScoringService(settings).run(use_llm=False)
    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT input_hash FROM job_scores WHERE job_id = %s", (job_id,)
        )
        assert cur.fetchone() is not None
    # The previously-scored job must not be in the new consideration set.
    assert job_id not in _open_unscored_ids(settings)


def _open_unscored_ids(settings):
    """Helper: ids the next run would reconsider (changed/new)."""
    from jobsearch.scoring.engine import ScoringEngine
    from jobsearch.scoring.profile import Profile, ScoringConfig
    from jobsearch.scoring.repository import select_candidates
    from jobsearch.scoring.service import _needs_scoring

    engine = ScoringEngine(Profile.from_config(), ScoringConfig.from_config())
    cfg = ScoringConfig.from_config()
    with connect(settings.database_url) as conn:
        rows = select_candidates(conn)
    return {
        r.job_id
        for r in rows
        if _needs_scoring(r, cfg.scorer_version, False, engine)
    }


def test_changed_skills_trigger_rescore():
    settings = load_settings()
    with connect(DATABASE_URL) as conn:
        job_id, fp = _insert_job(conn, title="Android Engineer", skills=["Kotlin"])

    ScoringService(settings).run(use_llm=False)
    assert job_id not in _open_unscored_ids(settings)

    # Mutate the posting's skills -> the input hash changes -> reconsidered.
    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("UPDATE jobs SET skills = %s WHERE id = %s", (["Kotlin", "Flutter"], job_id))
    assert job_id in _open_unscored_ids(settings)
