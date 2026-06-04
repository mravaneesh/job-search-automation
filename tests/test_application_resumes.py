import pytest

from jobsearch.application.config import ApplicationConfig
from jobsearch.application.models import JobContext
from jobsearch.application.resumes import ResumeLibrary


@pytest.fixture(scope="module")
def lib():
    return ResumeLibrary.from_config()


def _job(role, matched=None, missing=None):
    return JobContext(
        job_id=1,
        company_name="Acme",
        role_category=role,
        title="Engineer",
        url="https://x/1",
        matched_skills=matched or [],
        missing_skills=missing or [],
    )


@pytest.mark.parametrize(
    "role,expected",
    [("android", "Android"), ("backend", "Backend"), ("ai_ml", "AI")],
)
def test_select_best_matches_role(lib, role, expected):
    resume, reason = lib.select_best(_job(role))
    assert resume.name == expected
    assert "Role match" in reason


def test_recommendations_emphasise_matched_and_flag_missing(lib):
    job = _job("android", matched=["Kotlin", "Android SDK"], missing=["Jetpack Compose"])
    resume, _ = lib.select_best(job)
    recs = " ".join(lib.recommendations(resume, job))
    assert "Kotlin" in recs
    assert "Jetpack Compose" in recs


def test_bullet_suggestions_count(lib):
    cfg = ApplicationConfig.from_config()
    job = _job("backend", matched=["Java", "Spring"])
    bullets = lib.bullet_suggestions(job, cfg.bullet_suggestions)
    assert len(bullets) == cfg.bullet_suggestions
    assert any("Java" in b for b in bullets)
