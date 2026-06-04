"""Deterministic draft generators: cover letters and recruiter outreach.

Pure functions, zero tokens. Each artifact carries a stable ``input_hash`` so
identical inputs are never regenerated (dedup at the DB layer). Drafts only —
nothing is ever sent.
"""

from __future__ import annotations

import hashlib

from jobsearch.application.config import Candidate, ResumeSpec
from jobsearch.application.models import (
    KIND_COVER_LETTER,
    KIND_FOLLOW_UP,
    KIND_LINKEDIN,
    KIND_RECRUITER_EMAIL,
    JobContext,
)

_LINKEDIN_LIMIT = 300  # LinkedIn connection-note character limit


def artifact_input_hash(
    kind: str,
    job: JobContext,
    *,
    resume: ResumeSpec | None = None,
    recruiter_name: str | None = None,
) -> str:
    parts = [
        kind,
        str(job.job_id),
        job.company_name.lower(),
        job.title.lower(),
        str(job.match_score or ""),
        "|".join(sorted(s.lower() for s in job.matched_skills)),
        "|".join(sorted(s.lower() for s in job.missing_skills)),
        (resume.name if resume else ""),
        (recruiter_name or "").lower(),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _top_skills(job: JobContext, n: int = 4) -> str:
    skills = job.matched_skills[:n]
    return ", ".join(skills) if skills else "my core engineering skills"


def cover_letter(candidate: Candidate, job: JobContext, resume: ResumeSpec | None) -> str:
    summary = candidate.summary or "I build reliable, well-architected software."
    themes = ", ".join(resume.themes[:3]) if resume and resume.themes else job.role_category
    sign = candidate.name
    contact = " · ".join(p for p in [candidate.email, candidate.phone] if p)
    return (
        f"Dear {job.company_name} Hiring Team,\n\n"
        f"I'm writing to apply for the {job.title} role at {job.company_name}. "
        f"{summary}\n\n"
        f"My work centres on {themes}, and my experience with {_top_skills(job)} maps "
        f"directly to what this role calls for. I'm drawn to {job.company_name} and would "
        f"bring a focus on shipping measurable, high-quality work.\n\n"
        f"I'd welcome the chance to discuss how I can contribute. Thank you for your "
        f"consideration.\n\n"
        f"Best regards,\n{sign}\n{contact}"
    )


def linkedin_message(candidate: Candidate, job: JobContext, recruiter_name: str | None) -> str:
    greeting = f"Hi {recruiter_name}," if recruiter_name else "Hi,"
    skills = ", ".join(job.matched_skills[:2]) or job.role_category
    msg = (
        f"{greeting} I'm a software engineer (~2 yrs) focused on {job.role_category}. "
        f"I saw the {job.title} opening at {job.company_name} — my {skills} background looks "
        f"like a strong fit. Would love to connect. — {candidate.name}"
    )
    if len(msg) > _LINKEDIN_LIMIT:
        msg = msg[: _LINKEDIN_LIMIT - 1].rstrip() + "…"
    return msg


def recruiter_email(candidate: Candidate, job: JobContext, recruiter_name: str | None) -> str:
    greeting = f"Hi {recruiter_name}," if recruiter_name else f"Hi {job.company_name} team,"
    contact = " · ".join(p for p in [candidate.email, candidate.phone, candidate.linkedin] if p)
    return (
        f"Subject: {job.title} at {job.company_name} — {candidate.name}\n\n"
        f"{greeting}\n\n"
        f"I'm reaching out about the {job.title} role at {job.company_name}. I'm a software "
        f"engineer with ~2 years of experience in {_top_skills(job)}, and I believe I'd be a "
        f"strong contributor to your team.\n\n"
        f"Role: {job.url}\n\n"
        f"I'd appreciate the chance to share more about my background. Thank you for your time.\n\n"
        f"Best regards,\n{candidate.name}\n{contact}"
    )


def follow_up(candidate: Candidate, job: JobContext, recruiter_name: str | None) -> str:
    greeting = f"Hi {recruiter_name}," if recruiter_name else "Hi,"
    return (
        f"{greeting}\n\n"
        f"I wanted to follow up on my application for the {job.title} role at "
        f"{job.company_name}. I remain very interested and would be glad to provide anything "
        f"helpful for your evaluation.\n\n"
        f"Thank you again for your time.\n\n"
        f"Best regards,\n{candidate.name}"
    )


# kind -> generator function (recruiter-aware where relevant)
GENERATORS = {
    KIND_COVER_LETTER: lambda c, j, resume, recruiter: cover_letter(c, j, resume),
    KIND_LINKEDIN: lambda c, j, resume, recruiter: linkedin_message(c, j, recruiter),
    KIND_RECRUITER_EMAIL: lambda c, j, resume, recruiter: recruiter_email(c, j, recruiter),
    KIND_FOLLOW_UP: lambda c, j, resume, recruiter: follow_up(c, j, recruiter),
}
