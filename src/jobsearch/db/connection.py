"""PostgreSQL connection helper (psycopg 3)."""

from __future__ import annotations

from contextlib import contextmanager

import psycopg


@contextmanager
def connect(database_url: str):
    """Yield a connection; commit on success, roll back on error."""
    conn = psycopg.connect(database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
