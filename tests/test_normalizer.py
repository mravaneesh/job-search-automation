from jobsearch.collectors.greenhouse import GreenhouseCollector
from jobsearch.models import RawJob
from jobsearch.normalize.locations import LocationFilter
from jobsearch.normalize.normalizer import Normalizer, parse_experience


def _backend_raw(location: str) -> RawJob:
    return RawJob(
        source="greenhouse",
        company_name="Acme",
        title="Backend Engineer",
        url="https://x/1",
        location=location,
        description_html="<p>Build services in Go.</p>",
    )


def test_location_filter_keeps_india_drops_foreign():
    lf = LocationFilter.from_config()
    assert lf.keep("Bengaluru, Karnataka, IND") is True
    assert lf.keep("Hyderabad") is True
    assert lf.keep("San Francisco, CA") is False
    assert lf.keep("London, UK") is False
    # "Indiana" must not be mistaken for India.
    assert lf.keep("Indianapolis, Indiana, USA") is False


def test_remote_scope_india_drops_foreign_remote():
    lf = LocationFilter.from_config()
    assert lf.remote_scope == "india"
    # Global / unscoped remote is kept.
    assert lf.keep("Remote") is True
    assert lf.keep("Anywhere") is True
    assert lf.keep("Fully Remote") is True
    assert lf.keep("Remote - India") is True
    # Remote tied to a foreign country is dropped under india scope.
    assert lf.keep("Remote - USA") is False
    assert lf.keep("Remote, Brazil") is False


def test_remote_scope_any_keeps_all_remote():
    lf = LocationFilter.from_config()
    lf.remote_scope = "any"
    assert lf.keep("Remote - USA") is True


def test_normalize_drops_foreign_onsite_role():
    assert Normalizer.default().normalize(_backend_raw("San Francisco, CA")) is None
    assert Normalizer.default().normalize(_backend_raw("Pune, India")) is not None


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
