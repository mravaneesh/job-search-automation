"""Command-line entrypoint: `python -m jobsearch <command>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jobsearch.config import load_settings
from jobsearch.db.migrate import run_migrations
from jobsearch.logging_config import configure_logging, get_logger
from jobsearch.pipeline import Pipeline, renormalize
from jobsearch.registry.loader import load_registry
from jobsearch.reporting.dashboard import build_dashboard_html
from jobsearch.reporting.service import ReportingService
from jobsearch.scoring.service import ScoringService

log = get_logger("cli")


def _cmd_migrate(_args, settings) -> int:
    applied = run_migrations(settings.database_url)
    if applied:
        log.info("migrations_applied", files=applied)
    else:
        log.info("migrations_up_to_date")
    return 0


def _cmd_collect(args, settings) -> int:
    pipeline = Pipeline(settings)
    summary = pipeline.run(
        sources=set(args.source) if args.source else None,
        companies=set(args.company) if args.company else None,
        dry_run=args.dry_run,
        limit=args.limit,
    )
    print("\n=== Collection summary ===")
    for r in summary.results:
        print(
            f"  {r.label:<24} [{r.source:<11}] found={r.found:<4} matched={r.matched:<4} "
            f"inserted={r.inserted:<4} updated={r.updated:<4} {r.status}"
        )
    totals = summary.totals
    print(
        f"--- totals: targets={totals['targets']} found={totals['found']} "
        f"matched={totals['matched']} inserted={totals['inserted']} "
        f"updated={totals['updated']} failed={totals['failed']} ---"
    )
    return 0


def _cmd_score(args, settings) -> int:
    use_llm = True if args.llm else (False if args.no_llm else None)
    service = ScoringService(settings)
    summary = service.run(
        dry_run=args.dry_run,
        limit=args.limit,
        rescore_all=args.rescore_all,
        use_llm=use_llm,
    )
    print("\n=== Scoring summary ===")
    print(f"  considered (new/changed): {summary.considered}")
    print(f"  scored:                   {summary.scored}")
    print(
        f"  priority:  HIGH={summary.by_priority.get('HIGH', 0)}  "
        f"MEDIUM={summary.by_priority.get('MEDIUM', 0)}  "
        f"LOW={summary.by_priority.get('LOW', 0)}"
    )
    if summary.llm_used:
        print(
            f"  llm:  calls={summary.llm_calls}  "
            f"tokens={summary.input_tokens + summary.output_tokens} "
            f"(in={summary.input_tokens} out={summary.output_tokens})"
        )
    else:
        print("  llm:  not used (deterministic scoring)")
    return 0


def _parse_day(value):
    from datetime import datetime

    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def _cmd_report(args, settings) -> int:
    service = ReportingService(settings)
    report = service.report(day=_parse_day(args.date))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "html" or path.suffix == ".html":
            path.write_text(build_dashboard_html(report))
        elif args.format == "markdown":
            path.write_text(report.to_markdown())
        else:
            path.write_text(report.to_text())
        log.info("report_written", path=str(path))
    else:
        rendered = {"markdown": report.to_markdown, "html": report.to_html}.get(
            args.format, report.to_text
        )()
        print(rendered)
    return 0


def _cmd_notify(args, settings) -> int:
    service = ReportingService(settings)
    summary = service.notify(
        day=_parse_day(args.date),
        dry_run=args.dry_run,
        only_channels=set(args.channel) if args.channel else None,
    )
    print("\n=== Notification summary ===")
    print(f"  pending (new/changed): {summary.pending}")
    print(f"  sent:    {summary.sent_channels or '(none)'}")
    print(f"  skipped: {summary.skipped_channels or '(none)'}")
    print(f"  marked notified: {summary.marked}")
    return 0


def _cmd_renormalize(_args, settings) -> int:
    updated = renormalize(settings)
    log.info("renormalized", updated=updated)
    return 0


def _cmd_list_targets(_args, _settings) -> int:
    reg = load_registry()
    print("Companies:")
    for c in reg.companies:
        token = f" token={c.token}" if c.token else ""
        print(f"  [{c.status:<11}] {c.name:<22} {c.source}{token}")
    print("Aggregators:")
    for a in reg.aggregators:
        print(f"  [{a.status:<11}] {a.source:<22} locations={a.locations}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jobsearch", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="apply database migrations")

    collect = sub.add_parser("collect", help="collect jobs from sources")
    collect.add_argument("--source", action="append", help="limit to a source (repeatable)")
    collect.add_argument("--company", action="append", help="limit to a company (repeatable)")
    collect.add_argument("--dry-run", action="store_true", help="collect but do not write to DB")
    collect.add_argument("--limit", type=int, help="cap raw jobs processed per target")

    score = sub.add_parser("score", help="score new/changed jobs against the profile")
    score.add_argument("--dry-run", action="store_true", help="score but do not write to DB")
    score.add_argument("--limit", type=int, help="cap number of jobs scored")
    score.add_argument(
        "--rescore-all", action="store_true", help="re-score every open job, not just new ones"
    )
    score.add_argument("--llm", action="store_true", help="force-enable LLM refinement")
    score.add_argument("--no-llm", action="store_true", help="force-disable LLM refinement")

    report = sub.add_parser("report", help="build the daily report / dashboard")
    report.add_argument("--date", help="report date YYYY-MM-DD (default: today, UTC)")
    report.add_argument(
        "--format", choices=["text", "markdown", "html"], default="text", help="output format"
    )
    report.add_argument("--output", help="write to this file (e.g. dashboard/index.html)")

    notify = sub.add_parser("notify", help="send notifications for new/changed matches")
    notify.add_argument("--date", help="report date YYYY-MM-DD (default: today, UTC)")
    notify.add_argument("--dry-run", action="store_true", help="resolve pending but do not send")
    notify.add_argument(
        "--channel", action="append", help="limit to a channel: telegram / email (repeatable)"
    )

    sub.add_parser("renormalize", help="re-run normalization over stored raw payloads")
    sub.add_parser("list-targets", help="print the registry coverage map")
    return parser


_COMMANDS = {
    "migrate": _cmd_migrate,
    "collect": _cmd_collect,
    "score": _cmd_score,
    "report": _cmd_report,
    "notify": _cmd_notify,
    "renormalize": _cmd_renormalize,
    "list-targets": _cmd_list_targets,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    configure_logging(settings.log_level)
    return _COMMANDS[args.command](args, settings)


if __name__ == "__main__":
    sys.exit(main())
