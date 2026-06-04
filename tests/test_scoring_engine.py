import pytest

from jobsearch.scoring.engine import ScoringEngine
from jobsearch.scoring.models import JobInput
from jobsearch.scoring.profile import Profile, ScoringConfig


@pytest.fixture(scope="module")
def engine():
    return ScoringEngine(Profile.from_config(), ScoringConfig.from_config())


def _job(**kw):
    base = dict(
        job_id=1,
        company_name="Acme",
        role_category="android",
        title="Android Engineer",
        location="Bengaluru, India",
        experience="2+ years",
        employment_type="Full-time",
        skills=["Kotlin", "Android SDK", "REST"],
        company_category="global",
    )
    base.update(kw)
    return JobInput(**base)


def test_strong_android_match_is_high(engine):
    r = engine.score(_job())
    assert r.role_category == "android"
    assert r.skill_score == 100  # all listed skills are in the profile
    assert r.missing_skills == []
    assert r.match_score >= 75
    assert r.priority == "HIGH"


def test_missing_skills_surface(engine):
    r = engine.score(_job(skills=["Kotlin", "Flutter", "Dart"]))
    assert "Kotlin" in r.matched_skills
    assert set(r.missing_skills) == {"Flutter", "Dart"}
    assert r.skill_score == pytest.approx(33, abs=1)


def test_senior_role_penalised(engine):
    junior = engine.score(_job(title="Android Engineer", experience="2+ years"))
    senior = engine.score(_job(title="Senior Staff Android Engineer", experience="8+ years"))
    assert senior.seniority_score < junior.seniority_score
    assert senior.experience_score < junior.experience_score
    assert senior.match_score < junior.match_score


def test_location_scoring(engine):
    # "Remote" is in the profile's preferred locations, so it scores 100.
    local = engine.score(_job(location="Bengaluru, India"))
    remote = engine.score(_job(location="Remote"))
    foreign = engine.score(_job(location="San Francisco, CA"))
    unknown = engine.score(_job(location=None))
    assert local.location_score == 100
    assert remote.location_score == 100
    assert foreign.location_score == 30
    assert unknown.location_score == 60


def test_stretch_role_capped_below_primary(engine):
    # Identical-quality jobs, different role priority -> stretch scores lower.
    android = engine.score(_job(role_category="android", title="Engineer", skills=["Kotlin"]))
    aiml = engine.score(
        _job(role_category="ai_ml", title="Engineer", skills=["Python"], experience="2+ years")
    )
    assert aiml.match_score < android.match_score


def test_priority_thresholds(engine):
    r = engine.score(
        _job(
            role_category="ai_ml",
            title="Senior Principal ML Engineer",
            experience="10+ years",
            location="Zurich, Switzerland",
            skills=["Rust", "C++", "CUDA"],
            company_category=None,
        )
    )
    assert r.priority == "LOW"


def test_input_hash_changes_with_inputs(engine):
    a = engine.input_hash(_job(skills=["Kotlin"]))
    b = engine.input_hash(_job(skills=["Kotlin", "Java"]))
    c = engine.input_hash(_job(skills=["Kotlin"]))
    assert a != b
    assert a == c
