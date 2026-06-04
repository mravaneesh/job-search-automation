from jobsearch.application.config import Candidate, ResumeSpec
from jobsearch.application.generate import (
    artifact_input_hash,
    cover_letter,
    follow_up,
    linkedin_message,
    recruiter_email,
)
from jobsearch.application.models import KIND_COVER_LETTER, JobContext


def _candidate():
    return Candidate(name="Avaneesh Pandey", email="a@x.com", summary="I build software.")


def _job(matched=None):
    return JobContext(
        job_id=7,
        company_name="Stripe",
        role_category="android",
        title="Android Engineer",
        url="https://x/7",
        matched_skills=matched or ["Kotlin", "MVVM"],
        missing_skills=["Jetpack Compose"],
    )


def _resume():
    return ResumeSpec("android", "Android", 1, ["Kotlin"], ["Android", "MVVM"])


def test_cover_letter_is_company_and_role_specific():
    letter = cover_letter(_candidate(), _job(), _resume())
    assert "Stripe" in letter
    assert "Android Engineer" in letter
    assert "Avaneesh Pandey" in letter
    assert "Kotlin" in letter


def test_linkedin_within_limit():
    msg = linkedin_message(_candidate(), _job(), "Dana")
    assert "Stripe" in msg
    assert "Dana" in msg
    assert len(msg) <= 300


def test_recruiter_email_has_subject():
    body = recruiter_email(_candidate(), _job(), None)
    assert body.startswith("Subject:")
    assert "Android Engineer" in body
    assert "https://x/7" in body


def test_follow_up_mentions_role():
    fu = follow_up(_candidate(), _job(), "Dana")
    assert "Android Engineer" in fu
    assert "Dana" in fu


def test_input_hash_stable_and_input_sensitive():
    a = artifact_input_hash(KIND_COVER_LETTER, _job(matched=["Kotlin"]), resume=_resume())
    b = artifact_input_hash(KIND_COVER_LETTER, _job(matched=["Kotlin"]), resume=_resume())
    c = artifact_input_hash(KIND_COVER_LETTER, _job(matched=["Kotlin", "Coroutines"]),
                            resume=_resume())
    assert a == b
    assert a != c
