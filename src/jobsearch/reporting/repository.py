"""Queries for the daily report and notification dedup."""

from __future__ import annotations

from datetime import date


def notification_fingerprint(priority: str, match_score: int) -> str:
    """The state we dedup on: a job re-notifies only when this changes."""
    return f"{priority}:{match_score}"


def count_jobs_found_today(conn, day: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM jobs WHERE discovered_date::date = %s", (day,)
        )
        return int(cur.fetchone()[0])


def role_priority_counts(conn, day: date) -> list[tuple[str, str, int]]:
    """(role_category, priority, count) for jobs discovered on ``day``."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT j.role_category, s.priority, count(*) "
            "FROM jobs j JOIN job_scores s ON s.job_id = j.id "
            "WHERE j.discovered_date::date = %s "
            "GROUP BY j.role_category, s.priority",
            (day,),
        )
        return [(r[0], r[1], int(r[2])) for r in cur.fetchall()]


def top_opportunities(conn, day: date, limit: int) -> list[tuple]:
    """Highest-scoring HIGH/MEDIUM jobs discovered on ``day``."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT j.company_name, j.role_category, j.title, s.match_score, s.priority, j.url "
            "FROM jobs j JOIN job_scores s ON s.job_id = j.id "
            "WHERE j.discovered_date::date = %s AND s.priority IN ('HIGH','MEDIUM') "
            "ORDER BY s.match_score DESC, j.id LIMIT %s",
            (day, limit),
        )
        return list(cur.fetchall())


def select_pending(conn, priorities: list[str]) -> list[dict]:
    """Jobs that should be notified: new or score-changed, with an eligible
    priority, that have not yet been notified at their current state."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT j.id, j.company_name, j.role_category, j.title, j.url, "
            "       s.match_score, s.priority "
            "FROM jobs j "
            "JOIN job_scores s ON s.job_id = j.id "
            "LEFT JOIN notifications n ON n.job_id = j.id "
            "WHERE s.priority = ANY(%s) "
            "  AND (n.job_id IS NULL "
            "       OR n.fingerprint <> (s.priority || ':' || s.match_score::text)) "
            "ORDER BY s.match_score DESC, j.id",
            (priorities,),
        )
        cols = [
            "job_id", "company_name", "role_category", "title", "url", "match_score", "priority"
        ]
        return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


def mark_notified(conn, pending: list[dict]) -> None:
    with conn.cursor() as cur:
        for job in pending:
            fp = notification_fingerprint(job["priority"], job["match_score"])
            cur.execute(
                "INSERT INTO notifications (job_id, fingerprint, priority, match_score) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (job_id) DO UPDATE SET "
                "fingerprint = EXCLUDED.fingerprint, priority = EXCLUDED.priority, "
                "match_score = EXCLUDED.match_score, notified_at = now()",
                (job["job_id"], fp, job["priority"], job["match_score"]),
            )
