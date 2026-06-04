"""Data models for application intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from jobsearch.application.config import ResumeSpec

# Artifact kinds (also the values stored in application_artifacts.kind).
KIND_COVER_LETTER = "cover_letter"
KIND_LINKEDIN = "linkedin"
KIND_RECRUITER_EMAIL = "recruiter_email"
KIND_FOLLOW_UP = "follow_up"
KIND_RECOMMENDATION = "recommendation"
KIND_BULLETS = "bullets"

# Application workflow statuses, in order.
APPLICATION_STATUSES = [
    "SAVED",
    "READY_TO_APPLY",
    "APPLIED",
    "RECRUITER_SCREEN",
    "ONLINE_ASSESSMENT",
    "TECHNICAL",
    "FINAL",
    "OFFER",
    "REJECTED",
]

# Recruiter response statuses.
RECRUITER_STATUSES = [
    "NOT_CONTACTED",
    "CONTACTED",
    "RESPONDED",
    "INTERVIEWING",
    "REJECTED",
]


@dataclass
class JobContext:
    """Everything Phase 4 needs about a job, assembled from existing tables."""

    job_id: int
    company_name: str
    role_category: str
    title: str
    url: str
    location: str | None = None
    company_category: str | None = None
    company_tier: str | None = None
    match_score: int | None = None
    priority: str | None = None
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    skill_score: int | None = None
    experience_score: int | None = None
    seniority_score: int | None = None
    location_score: int | None = None
    company_score: int | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None


@dataclass
class Recommendation:
    job_id: int
    match_score: int
    priority: str
    resume: ResumeSpec | None
    why: list[str]
    missing: list[str]
    resume_recommendations: list[str]
    bullet_suggestions: list[str]
    strategy: str

    def to_text(self, job: JobContext) -> str:
        lines = [
            f"MATCH SCORE: {self.match_score}   PRIORITY: {self.priority}",
            f"{job.company_name} — {job.title}",
        ]
        if self.resume:
            lines.append(f"Best resume: {self.resume.name} (v{self.resume.version})")
        lines.append("")
        lines.append("Why:")
        lines += [f"  - {w}" for w in self.why] or ["  - (insufficient data)"]
        lines.append("")
        lines.append("Missing:")
        lines += [f"  - {m}" for m in self.missing] or ["  - none"]
        lines.append("")
        lines.append("Resume recommendations:")
        lines += [f"  - {r}" for r in self.resume_recommendations] or ["  - none"]
        lines.append("")
        lines.append("Suggested bullet points:")
        lines += [f"  - {b}" for b in self.bullet_suggestions]
        lines.append("")
        lines.append(f"Recommendation: {self.strategy}")
        return "\n".join(lines)


@dataclass
class ApplicationRow:
    id: int
    job_id: int
    status: str
    company_name: str
    title: str
    priority: str | None
    match_score: int | None
    application_date: date | None
    last_update: str | None
    recruiter_id: int | None
    resume_id: int | None
    notes: str | None
