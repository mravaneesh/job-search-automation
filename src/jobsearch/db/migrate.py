"""Apply plain versioned SQL migrations from migrations/*.sql."""

from __future__ import annotations

from pathlib import Path

from jobsearch.config import MIGRATIONS_DIR
from jobsearch.db.connection import connect

_TRACKING = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _applied(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def run_migrations(database_url: str, migrations_dir: Path | None = None) -> list[str]:
    """Apply all pending migrations in filename order. Returns applied names."""
    migrations_dir = migrations_dir or MIGRATIONS_DIR
    files = sorted(p for p in migrations_dir.glob("*.sql"))
    applied: list[str] = []
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(_TRACKING)
        done = _applied(conn)
        for path in files:
            if path.name in done:
                continue
            sql = path.read_text()
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                )
            applied.append(path.name)
    return applied
