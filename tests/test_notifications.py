"""DB-backed notification dedup tests.

Verifies the core Phase 3 guarantee: a job is notified when new or
score-changed, but never re-notified at an unchanged state.
"""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest

from jobsearch.db.connection import connect
from jobsearch.db.migrate import run_migrations
from jobsearch.reporting import repository as repo
from jobsearch.reporting.config import ReportingConfig
from jobsearch.reporting.service import build_daily_report

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    run_migrations(DATABASE_URL)


def _insert_scored_job(conn, *, priority="HIGH", match_score=90, role="android"):
    fp = uuid.uuid4().hex
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (company_name, role_category, title, source, url, fingerprint) "
            "VALUES ('Acme', %s, 'Android Engineer', 'greenhouse', %s, %s) RETURNING id",
            (role, f"https://x/{fp}", fp),
        )
        job_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO job_scores (job_id, role_category, match_score, skill_score, "
            "experience_score, location_score, seniority_score, company_score, "
            "interview_likelihood, priority, scorer_version, scored_by, input_hash) "
            "VALUES (%s, %s, %s, 90, 90, 90, 90, 90, 90, %s, 1, 'deterministic', %s)",
            (job_id, role, match_score, priority, fp),
        )
    return job_id


def _ids(pending):
    return {p["job_id"] for p in pending}


def test_new_job_is_pending_then_marked():
    cfg = ReportingConfig.from_config()
    with connect(DATABASE_URL) as conn:
        job_id = _insert_scored_job(conn, priority="HIGH", match_score=90)

    with connect(DATABASE_URL) as conn:
        pending = repo.select_pending(conn, cfg.notify_priorities)
        assert job_id in _ids(pending)
        repo.mark_notified(conn, [p for p in pending if p["job_id"] == job_id])

    # Already notified at this state -> no longer pending.
    with connect(DATABASE_URL) as conn:
        assert job_id not in _ids(repo.select_pending(conn, cfg.notify_priorities))


def test_score_change_makes_job_pending_again():
    cfg = ReportingConfig.from_config()
    with connect(DATABASE_URL) as conn:
        job_id = _insert_scored_job(conn, priority="MEDIUM", match_score=60)
        pending = repo.select_pending(conn, cfg.notify_priorities)
        repo.mark_notified(conn, [p for p in pending if p["job_id"] == job_id])

    with connect(DATABASE_URL) as conn:
        assert job_id not in _ids(repo.select_pending(conn, cfg.notify_priorities))
        # Score changes -> fingerprint differs -> pending again.
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE job_scores SET match_score = 95, priority = 'HIGH' WHERE job_id = %s",
                (job_id,),
            )

    with connect(DATABASE_URL) as conn:
        assert job_id in _ids(repo.select_pending(conn, cfg.notify_priorities))


def test_low_priority_never_pending():
    cfg = ReportingConfig.from_config()
    with connect(DATABASE_URL) as conn:
        job_id = _insert_scored_job(conn, priority="LOW", match_score=20)
    with connect(DATABASE_URL) as conn:
        assert job_id not in _ids(repo.select_pending(conn, cfg.notify_priorities))


def test_daily_report_counts_today():
    cfg = ReportingConfig.from_config()
    with connect(DATABASE_URL) as conn:
        _insert_scored_job(conn, priority="HIGH", match_score=88, role="backend")
        report = build_daily_report(conn, date.today(), cfg)
    assert report.jobs_found_today >= 1
    assert any(rb.role == "backend" for rb in report.roles)
    assert len(report.top_opportunities) >= 1
