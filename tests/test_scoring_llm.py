import json

from jobsearch.scoring import llm
from jobsearch.scoring.engine import ScoringEngine
from jobsearch.scoring.models import JobInput
from jobsearch.scoring.profile import Profile, ScoringConfig


def _setup():
    profile = Profile.from_config()
    config = ScoringConfig.from_config()
    engine = ScoringEngine(profile, config)
    job = JobInput(
        job_id=42,
        company_name="Acme",
        role_category="android",
        title="Android Engineer",
        location="Remote",
        experience="2+ years",
        employment_type="Full-time",
        skills=["Kotlin", "Flutter"],
        company_category="global",
    )
    return profile, config, engine, job


def test_payload_is_structured_only():
    profile, _config, engine, job = _setup()
    result = engine.score(job)
    payload = llm.build_batch_payload([(job, result)], profile)

    assert len(payload) == 1
    entry = payload[0]
    assert entry["ref"] == 42
    assert entry["role_priority"] == "primary"
    assert entry["matched_skills"] == ["Kotlin"]
    assert entry["missing_skills"] == ["Flutter"]
    # No description / HTML / raw content ever reaches the model.
    serialized = json.dumps(payload).lower()
    assert "description" not in serialized
    assert "<" not in serialized


def test_system_prompt_is_stable_and_has_no_volatile_content():
    profile, config, _engine, _job = _setup()
    a = llm.build_system_prompt(profile, config)
    b = llm.build_system_prompt(profile, config)
    assert a == b  # deterministic -> cache-friendly
    assert "~2 years" in a
    assert "android" in a


def test_parse_results_clamps_and_maps():
    text = json.dumps(
        {"results": [{"ref": 1, "likelihood": 150}, {"ref": 2, "likelihood": -5, "note": "x"}]}
    )
    parsed = llm.parse_results(text)
    assert parsed == {1: 100, 2: 0}


def test_estimate_max_tokens_bounded():
    assert llm.estimate_max_tokens(1) < llm.estimate_max_tokens(15)
    assert llm.estimate_max_tokens(1000) <= 4096
