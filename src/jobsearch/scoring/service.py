"""Scoring orchestration: pick new/changed jobs, score, optionally refine, store."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from jobsearch.config import Settings
from jobsearch.db.connection import connect
from jobsearch.logging_config import get_logger
from jobsearch.scoring import llm
from jobsearch.scoring import repository as repo
from jobsearch.scoring.engine import ScoringEngine
from jobsearch.scoring.models import ScoreResult
from jobsearch.scoring.profile import Profile, ScoringConfig

log = get_logger("scoring")


@dataclass
class ScoringSummary:
    considered: int = 0
    scored: int = 0
    by_priority: dict[str, int] = field(default_factory=lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0})
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    llm_used: bool = False


def _needs_scoring(row, scorer_version: int, rescore_all: bool, engine: ScoringEngine) -> bool:
    if rescore_all or row.input_hash is None:
        return True
    if row.scorer_version != scorer_version:
        return True
    # Inputs changed since last scored (e.g. collector refreshed the posting).
    return engine.input_hash(row.to_input()) != row.input_hash


def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


class ScoringService:
    def __init__(
        self,
        settings: Settings,
        profile: Profile | None = None,
        config: ScoringConfig | None = None,
    ):
        self._settings = settings
        self._profile = profile or Profile.from_config()
        self._config = config or ScoringConfig.from_config()
        self._engine = ScoringEngine(self._profile, self._config)

    def run(
        self,
        *,
        dry_run: bool = False,
        limit: int | None = None,
        rescore_all: bool = False,
        use_llm: bool | None = None,
    ) -> ScoringSummary:
        summary = ScoringSummary()
        cfg = self._config

        with connect(self._settings.database_url) as conn:
            rows = repo.select_candidates(conn)
            todo = [
                r
                for r in rows
                if _needs_scoring(r, cfg.scorer_version, rescore_all, self._engine)
            ]
            summary.considered = len(todo)
            if limit:
                todo = todo[:limit]

            jobs = [r.to_input() for r in todo]
            results: list[ScoreResult] = [self._engine.score(j) for j in jobs]

            want_llm = cfg.use_llm if use_llm is None else use_llm
            if want_llm:
                self._refine_with_llm(conn, jobs, results, summary)

            if not dry_run:
                run_id = repo.start_run(conn)
                for r in results:
                    repo.upsert_score(conn, r, cfg.scorer_version)
                    summary.by_priority[r.priority] = summary.by_priority.get(r.priority, 0) + 1
                summary.scored = len(results)
                repo.finish_run(
                    conn,
                    run_id,
                    considered=summary.considered,
                    scored=summary.scored,
                    llm_calls=summary.llm_calls,
                    input_tokens=summary.input_tokens,
                    output_tokens=summary.output_tokens,
                    status="success",
                )
            else:
                for r in results:
                    summary.by_priority[r.priority] = summary.by_priority.get(r.priority, 0) + 1

        log.info(
            "scoring_complete",
            considered=summary.considered,
            scored=summary.scored,
            high=summary.by_priority.get("HIGH", 0),
            llm_calls=summary.llm_calls,
            tokens=summary.input_tokens + summary.output_tokens,
        )
        return summary

    def _refine_with_llm(self, conn, jobs, results, summary) -> None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            log.warning("llm_skipped", reason="ANTHROPIC_API_KEY not set")
            return

        budget = self._config.max_tokens_per_day
        spent_today = repo.tokens_used_today(conn)
        if spent_today >= budget:
            log.warning("llm_skipped", reason="daily token budget exhausted", spent=spent_today)
            return

        by_id = {r.job_id: i for i, r in enumerate(results)}
        items = list(zip(jobs, results, strict=True))
        for batch in _chunks(items, self._config.batch_size):
            if spent_today >= budget:
                log.warning("llm_budget_reached", spent=spent_today)
                break
            try:
                overrides, usage = llm.score_batch(batch, self._profile, self._config)
            except Exception as exc:  # noqa: BLE001 — fall back to deterministic
                log.warning("llm_batch_failed", error=str(exc))
                break

            summary.llm_used = True
            summary.llm_calls += 1
            summary.input_tokens += usage.input_tokens
            summary.output_tokens += usage.output_tokens
            spent_today += usage.input_tokens + usage.output_tokens

            for job_id, likelihood in overrides.items():
                idx = by_id.get(job_id)
                if idx is None:
                    continue
                job = jobs[idx]
                results[idx] = self._engine.with_interview(
                    job.role_category, results[idx], likelihood, self._config.model
                )
