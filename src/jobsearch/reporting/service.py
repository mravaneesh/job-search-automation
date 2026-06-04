"""Reporting + notification orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from jobsearch.config import Settings
from jobsearch.db.connection import connect
from jobsearch.logging_config import get_logger
from jobsearch.reporting import repository as repo
from jobsearch.reporting.channels import Message, build_channels
from jobsearch.reporting.config import ReportingConfig
from jobsearch.reporting.report import DailyReport

log = get_logger("reporting")


def _today() -> date:
    return datetime.now(UTC).date()


def build_daily_report(conn, day: date, config: ReportingConfig) -> DailyReport:
    return DailyReport.build(
        day=day,
        jobs_found_today=repo.count_jobs_found_today(conn, day),
        count_rows=repo.role_priority_counts(conn, day),
        opp_rows=repo.top_opportunities(conn, day, config.top_opportunities),
        config=config,
    )


@dataclass
class NotifySummary:
    pending: int = 0
    sent_channels: list[str] = field(default_factory=list)
    skipped_channels: list[str] = field(default_factory=list)
    marked: bool = False


class ReportingService:
    def __init__(self, settings: Settings, config: ReportingConfig | None = None):
        self._settings = settings
        self._config = config or ReportingConfig.from_config()

    def report(self, day: date | None = None) -> DailyReport:
        day = day or _today()
        with connect(self._settings.database_url) as conn:
            return build_daily_report(conn, day, self._config)

    def notify(
        self,
        *,
        day: date | None = None,
        dry_run: bool = False,
        only_channels: set[str] | None = None,
    ) -> NotifySummary:
        day = day or _today()
        summary = NotifySummary()

        with connect(self._settings.database_url) as conn:
            report = build_daily_report(conn, day, self._config)
            pending = repo.select_pending(conn, self._config.notify_priorities)
            report.new_or_updated = len(pending)
            summary.pending = len(pending)

            # Avoid duplicate / empty notifications: only send when something is new.
            if not pending:
                log.info("notify_nothing_pending", day=day.isoformat())
                return summary

            message = Message(
                subject=f"[Job Search] {len(pending)} new/updated matches — {day.isoformat()}",
                text=report.to_text(),
                html=report.to_html(),
                telegram_html=report.to_telegram_html(),
            )

            channels = build_channels(only_channels)
            configured = [c for c in channels if c.is_configured()]
            summary.skipped_channels = [c.name for c in channels if not c.is_configured()]

            if not configured:
                log.warning("notify_no_channels", skipped=summary.skipped_channels)
                return summary

            for channel in configured:
                if dry_run:
                    log.info("notify_dry_run", channel=channel.name, pending=len(pending))
                    summary.sent_channels.append(channel.name)
                    continue
                if channel.send(message):
                    summary.sent_channels.append(channel.name)
                else:
                    summary.skipped_channels.append(channel.name)

            # Only record as notified if at least one real send succeeded.
            if summary.sent_channels and not dry_run:
                repo.mark_notified(conn, pending)
                summary.marked = True

        log.info(
            "notify_complete",
            pending=summary.pending,
            sent=summary.sent_channels,
            skipped=summary.skipped_channels,
            marked=summary.marked,
        )
        return summary
