"""End-to-end application-intelligence tests against a live PostgreSQL DB.

Skipped unless DATABASE_URL is set. Covers tracking, artifact dedup, the
generation gates, salary backfill, and tier sync.
"""

from __future__ import annotations

import os
import uuid

import pytest

from jobsearch.application import repository as repo
from jobsearch.application.service import ApplicationService
from jobsearch.config import load_settings
from jobsearch.db.connection import connect
from jobsearch.db.migrate import run_migrations

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    run_migrations(DATABASE_URL)


def _seed_job(
    *,
    priority="HIGH",
    score=90,
    role="android",
    matched=("Kotlin", "MVVM"),
    missing=("Jetpack Compose",),
    company="Stripe",
    category="global",
    description=None,
):
    fp = uuid.uuid4().hex
    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO companies (name, category, status) VALUES (%s, %s, 'implemented') "
            "ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category RETURNING id",
            (company, category),
        )
        company_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO jobs (company_id, company_name, role_category, title, source, url, "
            "location, description, fingerprint) VALUES "
            "(%s, %s, %s, 'Android Engineer', 'greenhouse', %s, 'Remote', %s, %s) RETURNING id",
            (company_id, company, role, f"https://x/{fp}", description, fp),
        )
        job_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO job_scores (job_id, role_category, match_score, skill_score, "
            "experience_score, location_score, seniority_score, company_score, "
            "interview_likelihood, matched_skills, missing_skills, priority, scorer_version, "
            "scored_by, input_hash) VALUES (%s, %s, %s, 90, 85, 100, 90, 90, 88, %s, %s, %s, 1, "
            "'deterministic', %s)",
            (job_id, role, score, list(matched), list(missing), priority, fp),
        )
    return job_id


def _svc():
    return ApplicationService(load_settings())


# ---- tracking --------------------------------------------------------------

def test_application_lifecycle():
    job_id = _seed_job()
    svc = _svc()
    svc.create_application(job_id, status="SAVED")
    assert svc.update_application(job_id, status="APPLIED", notes="submitted")

    rows = svc.list_applications(status="APPLIED")
    mine = [r for r in rows if r.job_id == job_id]
    assert mine and mine[0].status == "APPLIED"


def test_recruiter_and_outreach_personalisation():
    job_id = _seed_job()
    svc = _svc()
    rid = svc.add_recruiter(name="Dana Recruiter", company="Stripe", email="dana@stripe.com")
    results = svc.generate_outreach(job_id, kinds=["linkedin"], recruiter_id=rid)
    assert results[0].status == "created"
    assert "Dana Recruiter" in results[0].content


# ---- generation gates + dedup ---------------------------------------------

def test_cover_letter_gate_and_dedup():
    svc = _svc()

    # HIGH + high score -> generated, then deduped.
    high = _seed_job(priority="HIGH", score=92)
    first = svc.generate_cover_letter(high)
    assert first.status == "created"
    assert first.generated_by == "deterministic"
    second = svc.generate_cover_letter(high)
    assert second.status == "exists"
    assert second.content == first.content

    # MEDIUM -> skipped by the gate, unless forced.
    medium = _seed_job(priority="MEDIUM", score=60)
    skipped = svc.generate_cover_letter(medium)
    assert skipped.status == "skipped"
    forced = svc.generate_cover_letter(medium, force=True)
    assert forced.status == "created"


def test_outreach_generates_all_kinds():
    job_id = _seed_job()
    results = _svc().generate_outreach(
        job_id, kinds=["linkedin", "recruiter_email", "follow_up"]
    )
    kinds = {r.kind for r in results}
    assert kinds == {"linkedin", "recruiter_email", "follow_up"}
    assert all(r.status == "created" for r in results)


def test_recommendation_stored():
    job_id = _seed_job(score=92)
    rec, job = _svc().recommend(job_id)
    assert rec.match_score == 92
    with connect(DATABASE_URL) as conn:
        content = repo.get_artifact(
            conn,
            job_id,
            "recommendation",
            __import__("jobsearch.application.generate", fromlist=["x"]).artifact_input_hash(
                "recommendation", job, resume=rec.resume
            ),
        )
    assert content and "MATCH SCORE: 92" in content


# ---- salary + tiers --------------------------------------------------------

def test_salary_backfill():
    _seed_job(description="Compensation: $150,000 - $200,000 per year")
    updated = _svc().backfill_salary()
    assert updated >= 1


def test_tiers_sync_sets_tier():
    job_id = _seed_job(company="Google", category="global")
    _svc().sync_tiers()
    with connect(DATABASE_URL) as conn:
        job = repo.fetch_job_context(conn, job_id)
    assert job.company_tier == "tier1"


def test_resume_sync_and_lookup():
    svc = _svc()
    svc.sync_resumes()
    with connect(DATABASE_URL) as conn:
        rid = repo.resume_id_for(conn, "android", "Android", 1)
    assert rid is not None


def test_generation_token_ledger_starts_zero_or_more():
    with connect(DATABASE_URL) as conn:
        assert repo.generation_tokens_today(conn) >= 0
        repo.record_generation(conn, "cover_letter", 100, 50)
    with connect(DATABASE_URL) as conn:
        assert repo.generation_tokens_today(conn) >= 150
