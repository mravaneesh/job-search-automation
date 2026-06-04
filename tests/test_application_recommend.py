import json

from jobsearch.application.config import ApplicationConfig, Candidate
from jobsearch.application.llm import build_system_prompt, build_user_message
from jobsearch.application.models import JobContext
from jobsearch.application.recommend import build_recommendation, strategy_for
from jobsearch.application.resumes import ResumeLibrary


def _job(score, **kw):
    base = dict(
        job_id=1,
        company_name="Stripe",
        role_category="android",
        title="Android Engineer",
        url="https://x/1",
        match_score=score,
        priority="HIGH",
        matched_skills=["Kotlin", "MVVM"],
        missing_skills=["Jetpack Compose"],
        skill_score=90,
        experience_score=85,
        seniority_score=90,
        location_score=100,
        company_tier="tier1",
    )
    base.update(kw)
    return JobContext(**base)


def test_strategy_thresholds():
    cfg = ApplicationConfig.from_config()
    assert strategy_for(92, cfg) == "Apply immediately."
    assert strategy_for(74, cfg) == "Strong fit — apply."
    assert strategy_for(40, cfg).startswith("Consider")


def test_build_recommendation_matches_example_shape():
    cfg = ApplicationConfig.from_config()
    lib = ResumeLibrary.from_config()
    job = _job(92)
    rec = build_recommendation(job, lib, cfg)

    assert rec.match_score == 92
    assert rec.resume.name == "Android"
    assert any("Kotlin" in w for w in rec.why)
    assert any("Tier 1" in w for w in rec.why)
    assert "Jetpack Compose" in rec.missing
    assert rec.strategy == "Apply immediately."

    text = rec.to_text(job)
    assert "MATCH SCORE: 92" in text
    assert "Why:" in text
    assert "Missing:" in text
    assert "Recommendation: Apply immediately." in text


def test_llm_payload_is_structured_only():
    job = _job(92)
    user = build_user_message("cover_letter", job, "draft body")
    # Structured facts present; no HTML/raw description leaks.
    facts_line = user.splitlines()[1]
    facts = json.loads(facts_line)
    assert facts["company"] == "Stripe"
    assert facts["matched_skills"] == ["Kotlin", "MVVM"]
    assert "description" not in facts
    assert "<" not in user

    system = build_system_prompt(Candidate(name="Avaneesh Pandey", email="a@x.com"))
    assert build_system_prompt(Candidate(name="Avaneesh Pandey", email="a@x.com")) == system
    assert "never invent" in system.lower()
