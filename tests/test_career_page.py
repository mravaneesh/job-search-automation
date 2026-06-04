import yaml

from jobsearch.collectors.career_page import CareerPageCollector
from jobsearch.config import CONFIG_DIR


def _amazon_spec():
    data = yaml.safe_load((CONFIG_DIR / "companies.yaml").read_text())
    for c in data["companies"]:
        if c["name"] == "Amazon":
            return c["spec"]
    raise AssertionError("Amazon spec not found")


def test_career_page_parse(load_fixture):
    payload = load_fixture("amazon_jobs.json")
    spec = _amazon_spec()
    jobs = CareerPageCollector.parse(payload["jobs"], "Amazon", spec)

    assert len(jobs) == 2
    sde = jobs[0]
    assert sde.source == "career_page"
    assert sde.company_name == "Amazon"
    assert sde.source_job_id == "2500001"
    # Relative job_path is prefixed with url_prefix.
    assert sde.url == "https://www.amazon.jobs/en/jobs/2500001/software-development-engineer-backend"
    assert sde.location == "Bengaluru, KA, India"
    assert sde.employment_type == "Full Time"
    # "May 1, 2026" loose date parsing.
    assert sde.created_date.isoformat() == "2026-05-01"
