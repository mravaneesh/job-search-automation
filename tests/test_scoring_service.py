from jobsearch.scoring.engine import ScoringEngine
from jobsearch.scoring.models import JobInput
from jobsearch.scoring.profile import Profile, ScoringConfig
from jobsearch.scoring.repository import CandidateRow
from jobsearch.scoring.service import _needs_scoring


def _engine():
    return ScoringEngine(Profile.from_config(), ScoringConfig.from_config())


def _row(input_hash, scorer_version):
    return CandidateRow(
        (
            1,
            "Acme",
            "android",
            "Android Engineer",
            "Remote",
            "2+ years",
            "Full-time",
            ["Kotlin"],
            "global",
            input_hash,
            scorer_version,
        )
    )


def test_unscored_job_needs_scoring():
    engine = _engine()
    row = _row(None, None)
    assert _needs_scoring(row, scorer_version=1, rescore_all=False, engine=engine)


def test_unchanged_job_is_skipped():
    engine = _engine()
    current = engine.input_hash(_row(None, None).to_input())
    row = _row(current, 1)
    assert not _needs_scoring(row, scorer_version=1, rescore_all=False, engine=engine)


def test_changed_inputs_trigger_rescore():
    engine = _engine()
    row = _row("stale-hash", 1)
    assert _needs_scoring(row, scorer_version=1, rescore_all=False, engine=engine)


def test_scorer_version_bump_triggers_rescore():
    engine = _engine()
    current = engine.input_hash(_row(None, None).to_input())
    row = _row(current, 0)  # scored under an older version
    assert _needs_scoring(row, scorer_version=1, rescore_all=False, engine=engine)


def test_rescore_all_forces_rescore():
    engine = _engine()
    current = engine.input_hash(_row(None, None).to_input())
    row = _row(current, 1)
    assert _needs_scoring(row, scorer_version=1, rescore_all=True, engine=engine)


def test_with_interview_recomputes_match_score():
    engine = _engine()
    job = JobInput(
        job_id=1,
        company_name="Acme",
        role_category="android",
        title="Android Engineer",
        location="Remote",
        experience="2+ years",
        employment_type="Full-time",
        skills=["Kotlin"],
        company_category="global",
    )
    base = engine.score(job)
    bumped = engine.with_interview("android", base, 100, "claude-opus-4-8")
    dropped = engine.with_interview("android", base, 0, "claude-opus-4-8")
    assert bumped.interview_likelihood == 100
    assert bumped.scored_by == "claude-opus-4-8"
    assert bumped.match_score > base.match_score >= dropped.match_score
    # Other dimensions are untouched by the interview override.
    assert bumped.skill_score == base.skill_score
