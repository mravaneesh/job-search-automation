"""Render a standalone static HTML dashboard from a DailyReport."""

from __future__ import annotations

from datetime import UTC, datetime

from jobsearch.reporting.report import DailyReport

_STYLE = """
:root { color-scheme: light dark; }
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
       margin: 2rem auto; max-width: 960px; padding: 0 1rem; line-height: 1.5; }
h1 { margin-bottom: 0; }
.meta { color: #888; margin-top: .25rem; }
table { border-collapse: collapse; width: 100%; margin: .5rem 0 1.5rem; }
th, td { text-align: left; padding: .5rem .6rem; border-bottom: 1px solid #ddd; }
th { background: rgba(127,127,127,.12); }
.cards { display: flex; gap: 1rem; flex-wrap: wrap; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.25rem; min-width: 140px; }
.card .n { font-size: 1.8rem; font-weight: 700; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def build_dashboard_html(report: DailyReport) -> str:
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    cards = "".join(
        f'<div class="card"><div class="n">{rb.high}/{rb.medium}</div>'
        f"<div>{rb.label}<br><small>High / Medium</small></div></div>"
        for rb in report.roles
    )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Job Search Dashboard — {report.day.isoformat()}</title>"
        f"<style>{_STYLE}</style></head><body>"
        "<h1>Job Search Dashboard</h1>"
        f'<p class="meta">Report for {report.day.isoformat()} · generated {generated}</p>'
        '<div class="cards">'
        f'<div class="card"><div class="n">{report.jobs_found_today}</div>'
        f"<div>{report.found_label}</div></div>"
        f"{cards}</div>"
        f"{report.to_html()}"
        "</body></html>"
    )
