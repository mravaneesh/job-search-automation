from jobsearch.collectors.greenhouse import GreenhouseCollector


def test_greenhouse_parse(load_fixture):
    payload = load_fixture("greenhouse_jobs.json")
    jobs = GreenhouseCollector.parse(payload, "Acme")

    assert len(jobs) == 3
    backend = jobs[0]
    assert backend.source == "greenhouse"
    assert backend.company_name == "Acme"
    assert backend.title == "Senior Backend Engineer"
    assert backend.source_job_id == "100001"
    assert backend.url == "https://boards.greenhouse.io/acme/jobs/100001"
    assert backend.location == "Bengaluru, India"
    # first_published is preferred over updated_at.
    assert backend.created_date.isoformat() == "2026-04-15"
    # Content is HTML-escaped in the payload; collector keeps it raw for the
    # normalizer to convert.
    assert "distributed systems" in backend.description_html
