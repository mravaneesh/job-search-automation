"""Data models for the scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field

# How the interview-likelihood dimension was produced.
SCORED_BY_DETERMINISTIC = "deterministic"


@dataclass
class JobInput:
    """The structured, deterministic inputs a job contributes to scoring.

    Note: there is no description/HTML here — only structured fields. This is
    exactly the surface that may be forwarded to the LLM.
    """

    job_id: int
    company_name: str
    role_category: str
    title: str
    location: str | None
    experience: str | None
    employment_type: str | None
    skills: list[str] = field(default_factory=list)
    company_category: str | None = None


@dataclass
class ScoreResult:
    job_id: int
    role_category: str
    skill_score: int
    experience_score: int
    location_score: int
    seniority_score: int
    company_score: int
    interview_likelihood: int
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: int
    priority: str
    input_hash: str
    scored_by: str = SCORED_BY_DETERMINISTIC
