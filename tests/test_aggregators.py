from jobsearch.collectors.linkedin import LinkedInCollector


def test_linkedin_parse(load_fixture):
    html = load_fixture("linkedin_results.html")
    jobs = LinkedInCollector.parse(html)

    # Two valid cards; the card without a link is skipped.
    assert len(jobs) == 2
    first = jobs[0]
    assert first.source == "linkedin"
    assert first.title == "Android Engineer"
    assert first.company_name == "Acme Corp"
    assert first.location == "Bengaluru, India"
    # Query string is stripped from the URL.
    assert first.url == "https://www.linkedin.com/jobs/view/111"


def test_linkedin_build_url():
    collector = LinkedInCollector(settings=None)
    url = collector.build_url("Backend Engineer", "India")
    assert "keywords=Backend+Engineer" in url
    assert "location=India" in url
