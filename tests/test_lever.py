from jobsearch.collectors.lever import LeverCollector


def test_lever_parse(load_fixture):
    payload = load_fixture("lever_jobs.json")
    jobs = LeverCollector.parse(payload, "Acme")

    assert len(jobs) == 2
    ml = jobs[0]
    assert ml.source == "lever"
    assert ml.title == "Machine Learning Engineer"
    assert ml.source_job_id == "abc-123"
    assert ml.url == "https://jobs.lever.co/acme/abc-123"
    assert ml.location == "Bengaluru"
    assert ml.employment_type == "Full-time"
    assert ml.description_text == "Work on deep learning and LLM systems with PyTorch."
    assert ml.created_date.isoformat() == "2024-05-01"
