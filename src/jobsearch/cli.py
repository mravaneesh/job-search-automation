"""Command-line entrypoint: `python -m jobsearch <command>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jobsearch.application.models import (
    KIND_FOLLOW_UP,
    KIND_LINKEDIN,
    KIND_RECRUITER_EMAIL,
)
from jobsearch.application.service import ApplicationService
from jobsearch.config import load_settings
from jobsearch.db.migrate import run_migrations
from jobsearch.logging_config import configure_logging, get_logger
from jobsearch.pipeline import Pipeline, renormalize
from jobsearch.registry.loader import load_registry
from jobsearch.reporting.dashboard import build_dashboard_html
from jobsearch.reporting.service import ReportingService
from jobsearch.scoring.service import ScoringService

_OUTREACH_KINDS = {
    "linkedin": [KIND_LINKEDIN],
    "email": [KIND_RECRUITER_EMAIL],
    "followup": [KIND_FOLLOW_UP],
    "all": [KIND_LINKEDIN, KIND_RECRUITER_EMAIL, KIND_FOLLOW_UP],
}

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


def _llm_flag(args):
    return True if args.llm else (False if getattr(args, "no_llm", False) else None)


def _cmd_application_create(args, settings) -> int:
    app_id = ApplicationService(settings).create_application(
        args.job, status=args.status, notes=args.notes
    )
    print(f"application #{app_id} for job {args.job} created (status={args.status})")
    return 0


def _cmd_application_update(args, settings) -> int:
    ok = ApplicationService(settings).update_application(
        args.job,
        status=args.status,
        recruiter_id=args.recruiter,
        resume_id=args.resume,
        notes=args.notes,
        application_date=_parse_day(args.date),
    )
    print("updated" if ok else f"no application found for job {args.job} (run application-create)")
    return 0 if ok else 1


def _cmd_application_list(args, settings) -> int:
    rows = ApplicationService(settings).list_applications(status=args.status, limit=args.limit)
    print(f"\n=== Applications ({len(rows)}) ===")
    for r in rows:
        score = f"{r.match_score}" if r.match_score is not None else "-"
        print(
            f"  job {r.job_id:<5} [{r.status:<17}] {r.company_name[:20]:<20} "
            f"{r.title[:34]:<34} score={score} pri={r.priority or '-'}"
        )
    return 0


def _cmd_application_recommend(args, settings) -> int:
    rec, job = ApplicationService(settings).recommend(args.job)
    text = rec.to_text(job)
    if args.output:
        Path(args.output).write_text(text)
        log.info("recommendation_written", path=args.output)
    else:
        print(text)
    return 0


def _cmd_resume_select(args, settings) -> int:
    out = ApplicationService(settings).select_resume(args.job)
    resume = out["resume"]
    print(f"\nSelected resume: {resume.name} (v{resume.version})" if resume else "No resume")
    print(f"Reason: {out['reason']}")
    if out["recommendations"]:
        print("Recommendations:")
        for r in out["recommendations"]:
            print(f"  - {r}")
    if args.apply and resume:
        svc = ApplicationService(settings)
        svc.create_application(args.job)
        # resolve the resume id (sync to DB first so the FK exists)
        svc.sync_resumes()
        from jobsearch.application import repository as arepo
        from jobsearch.db.connection import connect

        with connect(settings.database_url) as conn:
            rid = arepo.resume_id_for(conn, resume.role_category, resume.name, resume.version)
        svc.update_application(args.job, resume_id=rid, resume_version=resume.version)
        print(f"Stored resume selection on the application (resume_id={rid}).")
    return 0


def _cmd_generate_cover_letter(args, settings) -> int:
    res = ApplicationService(settings).generate_cover_letter(
        args.job, force=args.force, use_llm=_llm_flag(args)
    )
    if res.status == "skipped":
        print(f"Cover letter skipped: {res.reason}.")
        print("Use --force to override the HIGH-priority/score gate.")
        return 0
    print(f"[{res.status}] generated_by={res.generated_by}")
    if args.output:
        Path(args.output).write_text(res.content)
        log.info("cover_letter_written", path=args.output)
    else:
        print("\n" + res.content)
    return 0


def _cmd_generate_outreach(args, settings) -> int:
    kinds = _OUTREACH_KINDS[args.kind]
    results = ApplicationService(settings).generate_outreach(
        args.job, kinds=kinds, recruiter_id=args.recruiter, use_llm=_llm_flag(args)
    )
    for res in results:
        print(f"\n--- {res.kind} [{res.status}] generated_by={res.generated_by} ---")
        print(res.content)
    return 0


def _cmd_recruiter_add(args, settings) -> int:
    rid = ApplicationService(settings).add_recruiter(
        name=args.name, company=args.company, linkedin_url=args.linkedin,
        email=args.email, notes=args.notes,
    )
    print(f"recruiter #{rid} created")
    return 0


def _cmd_salary_backfill(_args, settings) -> int:
    n = ApplicationService(settings).backfill_salary()
    log.info("salary_backfilled", updated=n)
    return 0


def _cmd_tiers_sync(_args, settings) -> int:
    n = ApplicationService(settings).sync_tiers()
    log.info("tiers_synced", companies=n)
    return 0


def _cmd_resumes_sync(_args, settings) -> int:
    n = ApplicationService(settings).sync_resumes()
    log.info("resumes_synced", resumes=n)
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

    # ---- Phase 4: application intelligence ----
    ac = sub.add_parser("application-create", help="start tracking an application for a job")
    ac.add_argument("--job", type=int, required=True)
    ac.add_argument("--status", default="SAVED")
    ac.add_argument("--notes")

    au = sub.add_parser("application-update", help="update an application's workflow state")
    au.add_argument("--job", type=int, required=True)
    au.add_argument("--status")
    au.add_argument("--recruiter", type=int, help="recruiter id")
    au.add_argument("--resume", type=int, help="resume id")
    au.add_argument("--notes")
    au.add_argument("--date", help="application date YYYY-MM-DD")

    al = sub.add_parser("application-list", help="list tracked applications")
    al.add_argument("--status")
    al.add_argument("--limit", type=int)

    ar = sub.add_parser("application-recommend", help="why-fit / missing / strategy for a job")
    ar.add_argument("--job", type=int, required=True)
    ar.add_argument("--output")

    rs = sub.add_parser("resume-select", help="select the best resume for a job")
    rs.add_argument("--job", type=int, required=True)
    rs.add_argument("--apply", action="store_true", help="store the selection on the application")

    gc = sub.add_parser("generate-cover-letter", help="generate a tailored cover letter draft")
    gc.add_argument("--job", type=int, required=True)
    gc.add_argument("--force", action="store_true", help="bypass the HIGH-priority/score gate")
    gc.add_argument("--llm", action="store_true", help="polish with the LLM (within budget)")
    gc.add_argument("--output")

    go = sub.add_parser("generate-outreach", help="generate recruiter outreach drafts")
    go.add_argument("--job", type=int, required=True)
    go.add_argument("--kind", choices=list(_OUTREACH_KINDS), default="all")
    go.add_argument("--recruiter", type=int, help="recruiter id (personalises the draft)")
    go.add_argument("--llm", action="store_true", help="polish with the LLM (within budget)")

    radd = sub.add_parser("recruiter-add", help="add a recruiter")
    radd.add_argument("--name", required=True)
    radd.add_argument("--company")
    radd.add_argument("--linkedin")
    radd.add_argument("--email")
    radd.add_argument("--notes")

    sub.add_parser("salary-backfill", help="extract salary for jobs that lack it")
    sub.add_parser("tiers-sync", help="persist company tiers from config onto companies")
    sub.add_parser("resumes-sync", help="persist master resumes from config into the DB")

    sub.add_parser("renormalize", help="re-run normalization over stored raw payloads")
    sub.add_parser("list-targets", help="print the registry coverage map")
    return parser


_COMMANDS = {
    "migrate": _cmd_migrate,
    "collect": _cmd_collect,
    "score": _cmd_score,
    "report": _cmd_report,
    "notify": _cmd_notify,
    "application-create": _cmd_application_create,
    "application-update": _cmd_application_update,
    "application-list": _cmd_application_list,
    "application-recommend": _cmd_application_recommend,
    "resume-select": _cmd_resume_select,
    "generate-cover-letter": _cmd_generate_cover_letter,
    "generate-outreach": _cmd_generate_outreach,
    "recruiter-add": _cmd_recruiter_add,
    "salary-backfill": _cmd_salary_backfill,
    "tiers-sync": _cmd_tiers_sync,
    "resumes-sync": _cmd_resumes_sync,
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
