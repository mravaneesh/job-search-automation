from jobsearch.collectors.ashby import AshbyCollector


def test_ashby_parse_skips_unlisted(load_fixture):
    payload = load_fixture("ashby_jobs.json")
    jobs = AshbyCollector.parse(payload, "Acme")

    # The unlisted job (isListed=false) must be dropped.
    assert len(jobs) == 2
    titles = {j.title for j in jobs}
    assert "Hidden Backend Role" not in titles

    backend = jobs[0]
    assert backend.source == "ashby"
    assert backend.source_job_id == "ash-1"
    assert backend.employment_type == "FullTime"
    assert backend.created_date.isoformat() == "2026-03-10"
