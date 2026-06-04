from jobsearch.collectors.greenhouse import GreenhouseCollector
from jobsearch.models import RawJob
from jobsearch.normalize.normalizer import Normalizer, parse_experience


def test_parse_experience_years():
    assert parse_experience("Backend Engineer", "Requires 5+ years of experience") == "5+ years"


def test_parse_experience_seniority():
    assert parse_experience("Senior Backend Engineer", None) == "Senior"
    assert parse_experience("Backend Engineering Intern", None) == "Internship"


def test_normalize_drops_non_target_role(load_fixture):
    payload = load_fixture("greenhouse_jobs.json")
    raw = GreenhouseCollector.parse(payload, "Acme")
    normalizer = Normalizer.default()

    results = [normalizer.normalize(r) for r in raw]
    kept = [j for j in results if j is not None]

    # The "Technical Recruiter" posting is dropped.
    assert len(kept) == 2
    roles = {j.role_category for j in kept}
    assert roles == {"backend", "android"}


def test_normalize_extracts_skills_and_fingerprint():
    raw = RawJob(
        source="greenhouse",
        company_name="Acme",
        title="Backend Engineer",
        url="https://x/1",
        location="Remote",
        description_html="<p>Build services in Go with Kafka and PostgreSQL.</p>",
    )
    job = Normalizer.default().normalize(raw)
    assert job is not None
    assert job.role_category == "backend"
    assert "Go" in job.skills and "Kafka" in job.skills
    assert job.description == "Build services in Go with Kafka and PostgreSQL."
    assert len(job.fingerprint) == 64  # sha256 hex
    assert job.source_priority == 20  # greenhouse
