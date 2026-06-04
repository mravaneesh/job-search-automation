from datetime import date

from jobsearch.reporting.config import ReportingConfig
from jobsearch.reporting.dashboard import build_dashboard_html
from jobsearch.reporting.report import DailyReport


def _report():
    cfg = ReportingConfig.from_config()
    count_rows = [
        ("android", "HIGH", 2),
        ("android", "MEDIUM", 1),
        ("backend", "HIGH", 1),
        ("ai_ml", "MEDIUM", 3),
    ]
    opp_rows = [
        ("Stripe", "android", "Android Engineer", 92, "HIGH", "https://x/1"),
        ("Razorpay", "backend", "Backend Engineer", 80, "HIGH", "https://x/2"),
    ]
    return DailyReport.build(date(2026, 6, 4), 7, count_rows, opp_rows, cfg)


def test_build_aggregates_counts_by_role():
    r = _report()
    by_role = {rb.role: rb for rb in r.roles}
    assert by_role["android"].high == 2
    assert by_role["android"].medium == 1
    assert by_role["backend"].high == 1
    assert by_role["ai_ml"].medium == 3
    # Roles with no jobs still appear with zeros.
    assert by_role["ai_ml"].high == 0


def test_text_report_has_required_sections():
    text = _report().to_text()
    assert "Jobs Found Today: 7" in text
    assert "Android:" in text
    assert "High Match:" in text
    assert "Medium Match:" in text
    assert "Top Opportunities:" in text
    assert "Stripe" in text and "https://x/1" in text


def test_top_opportunities_have_all_fields():
    r = _report()
    top = r.top_opportunities[0]
    assert top.company == "Stripe"
    assert top.role == "Android"  # label-mapped
    assert top.match_score == 92
    assert top.url == "https://x/1"


def test_html_escapes_and_links():
    cfg = ReportingConfig.from_config()
    r = DailyReport.build(
        date(2026, 6, 4),
        1,
        [("android", "HIGH", 1)],
        [("A&B <Co>", "android", "Eng <x>", 88, "HIGH", "https://x/1")],
        cfg,
    )
    html = r.to_html()
    assert "A&amp;B &lt;Co&gt;" in html
    assert "&lt;x&gt;" in html  # title escaped
    assert 'href="https://x/1"' in html


def test_dashboard_is_standalone_html():
    page = build_dashboard_html(_report())
    assert page.startswith("<!doctype html>")
    assert "Job Search Dashboard" in page
    assert "Jobs Found Today" in page


def test_all_matches_full_list_with_links():
    cfg = ReportingConfig.from_config()
    match_rows = [
        ("Airbnb", "android", "Android SWE", 94, "HIGH", "https://x/airbnb", "tier3", "Remote"),
        ("Amazon", "android", "SDE Android", 90, "HIGH", "https://x/amazon", "tier3", "Bengaluru"),
        ("Stripe", "backend", "Backend Eng", 70, "MEDIUM", "https://x/stripe", "tier1", "Remote"),
    ]
    r = DailyReport.build(date(2026, 6, 4), 50, [("android", "HIGH", 2)], [], cfg,
                          match_rows=match_rows)
    assert len(r.all_matches) == 3

    text = r.to_text()
    assert "All Matches (3)" in text
    assert "https://x/airbnb" in text and "https://x/amazon" in text and "https://x/stripe" in text

    html = r.to_html()
    assert "All Matches (3)" in html
    assert 'href="https://x/stripe"' in html
    assert "Bengaluru" in html  # location column present
