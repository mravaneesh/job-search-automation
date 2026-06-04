"""Deterministic application recommendations (why-fit / missing / strategy).

Built entirely from existing score data — no LLM, no tokens.
"""

from __future__ import annotations

from jobsearch.application.config import ApplicationConfig
from jobsearch.application.models import Recommendation
from jobsearch.application.resumes import ResumeLibrary


def strategy_for(match_score: int | None, config: ApplicationConfig) -> str:
    score = match_score or 0
    if score >= config.strategy_apply_immediately:
        return "Apply immediately."
    if score >= config.strategy_strong_apply:
        return "Strong fit — apply."
    return "Consider; tailor your resume before applying."


def build_why(job) -> list[str]:
    why: list[str] = []
    if job.matched_skills:
        top = ", ".join(job.matched_skills[:4])
        why.append(f"Strong skill match: {top}.")
    if (job.skill_score or 0) >= 70 and not job.matched_skills:
        why.append("Good overall skill alignment.")
    if (job.experience_score or 0) >= 70:
        why.append("Experience requirement aligns with your ~2 years.")
    if (job.seniority_score or 0) >= 70:
        why.append("Role seniority fits an IC / mid-level engineer.")
    if (job.location_score or 0) >= 90:
        why.append("Location / remote preference is a match.")
    if job.company_tier == "tier1":
        why.append("Tier 1 company — high-value opportunity.")
    if not why:
        why.append("Meets the basic role criteria.")
    return why


def build_recommendation(
    job, library: ResumeLibrary, config: ApplicationConfig
) -> Recommendation:
    resume, _reason = library.select_best(job)
    return Recommendation(
        job_id=job.job_id,
        match_score=job.match_score or 0,
        priority=job.priority or "LOW",
        resume=resume,
        why=build_why(job),
        missing=list(job.missing_skills),
        resume_recommendations=library.recommendations(resume, job),
        bullet_suggestions=library.bullet_suggestions(job, config.bullet_suggestions),
        strategy=strategy_for(job.match_score, config),
    )
