"""Repository tests against a live PostgreSQL database.

Skipped unless DATABASE_URL is set (CI provides a Postgres service). These
verify idempotent upsert and source-priority dedup behaviour end to end.
"""

from __future__ import annotations

import os
import uuid

import pytest

from jobsearch.db import repository as repo
from jobsearch.db.connection import connect
from jobsearch.db.migrate import run_migrations
from jobsearch.models import Job
from jobsearch.registry.loader import CompanyTarget

DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    run_migrations(DATABASE_URL)


def _job(fingerprint: str, *, source="greenhouse", priority=20, title="Backend Engineer") -> Job:
    return Job(
        company_name="Acme",
        role_category="backend",
        title=title,
        source=source,
        source_priority=priority,
        url=f"https://example.com/{fingerprint}",
        location="Remote",
        skills=["Go", "Kafka"],
        fingerprint=fingerprint,
        raw={"title": title},
    )


def test_upsert_is_idempotent():
    fp = uuid.uuid4().hex
    target = CompanyTarget(
        name="Acme", category="backend", source="greenhouse", status="implemented", token="acme"
    )
    with connect(DATABASE_URL) as conn:
        cid = repo.upsert_company(conn, target)
        assert repo.upsert_job(conn, _job(fp), cid) == "inserted"
        assert repo.upsert_job(conn, _job(fp), cid) == "updated"

    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM jobs WHERE fingerprint = %s", (fp,))
        assert cur.fetchone()[0] == 1


def test_higher_priority_source_wins():
    fp = uuid.uuid4().hex
    with connect(DATABASE_URL) as conn:
        # Lower priority (lever=30) inserted first.
        repo.upsert_job(conn, _job(fp, source="lever", priority=30, title="Backend Engineer"), None)
        # Higher priority (career_page=10) should overwrite canonical fields.
        repo.upsert_job(
            conn, _job(fp, source="career_page", priority=10, title="Backend Engineer II"), None
        )

    with connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT source, title, source_priority FROM jobs WHERE fingerprint = %s", (fp,))
        source, title, priority = cur.fetchone()
        assert source == "career_page"
        assert title == "Backend Engineer II"
        assert priority == 10
