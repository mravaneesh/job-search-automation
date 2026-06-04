"""Deterministic scoring. No LLM, no network — pure functions over JobInput.

Six dimensions are computed (skill, experience, location, seniority, company,
interview-likelihood), combined by configured weights into a 0-100 match score,
then mapped to a HIGH/MEDIUM/LOW priority. The interview-likelihood here is a
deterministic baseline; the LLM layer may later override just that dimension.
"""

from __future__ import annotations

import hashlib
import re

from jobsearch.scoring.models import SCORED_BY_DETERMINISTIC, JobInput, ScoreResult
from jobsearch.scoring.profile import Profile, ScoringConfig

_YEARS = re.compile(r"(\d{1,2})\s*\+?", re.IGNORECASE)

# Title/experience seniority label -> (experience_fit, seniority_fit) for a
# candidate at the junior/mid level (~2 years).
_SENIORITY_FIT = {
    "internship": (70, 60),
    "entry level": (100, 95),
    "junior": (100, 95),
    "lead": (35, 35),
    "senior": (45, 45),
    "staff": (25, 25),
    "principal": (15, 15),
}
_TITLE_SENIORITY = [
    ("intern", "internship"),
    ("principal", "principal"),
    ("staff", "staff"),
    ("senior", "senior"),
    (" sr ", "senior"),
    ("lead", "lead"),
    ("junior", "junior"),
    (" jr ", "junior"),
    ("new grad", "entry level"),
    ("entry level", "entry level"),
]


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


class ScoringEngine:
    def __init__(self, profile: Profile, config: ScoringConfig):
        self._profile = profile
        self._config = config

    # ---- input fingerprint (re-score guard) -------------------------------

    def input_hash(self, job: JobInput) -> str:
        parts = [
            str(self._config.scorer_version),
            job.role_category,
            (job.title or "").strip().lower(),
            (job.location or "").strip().lower(),
            (job.experience or "").strip().lower(),
            (job.employment_type or "").strip().lower(),
            (job.company_category or "").strip().lower(),
            "|".join(sorted(s.lower() for s in job.skills)),
        ]
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    # ---- individual dimensions --------------------------------------------

    def _skills(self, job: JobInput) -> tuple[int, list[str], list[str]]:
        profile_lower = self._profile.all_skills_lower
        matched, missing = [], []
        for skill in job.skills:
            (matched if skill.lower() in profile_lower else missing).append(skill)
        if not job.skills:
            return 50, [], []  # neutral when the posting lists no skills
        score = _clamp(100 * len(matched) / len(job.skills))
        return score, sorted(set(matched)), sorted(set(missing))

    def _experience(self, job: JobInput) -> int:
        text = (job.experience or "").lower()
        m = _YEARS.search(text)
        if m:
            required = int(m.group(1))
            diff = required - self._profile.experience_years
            if diff <= 0:
                return 100
            return _clamp(100 - diff * 20)
        for label, (exp_fit, _sen) in _SENIORITY_FIT.items():
            if label in text:
                return exp_fit
        return 60  # neutral when experience is unknown

    def _seniority(self, job: JobInput) -> int:
        title = f" {(job.title or '').lower()} "
        for needle, label in _TITLE_SENIORITY:
            if needle in title:
                return _SENIORITY_FIT.get(label, (90, 90))[1]
        return 90  # untitled seniority reads as IC/mid — a good fit

    def _location(self, job: JobInput) -> int:
        if not job.location:
            return 60
        loc = job.location.lower()
        if any(p.lower() in loc for p in self._profile.preferred_locations):
            return 100
        if "remote" in loc or "hybrid" in loc:
            return 90
        return 30

    def _company(self, job: JobInput) -> int:
        q = self._config.company_quality
        return q.get(job.company_category or "", q.get("default", 60))

    def _deterministic_interview(self, skill: int, experience: int, seniority: int) -> int:
        return _clamp(0.5 * skill + 0.25 * experience + 0.25 * seniority)

    # ---- assembly ----------------------------------------------------------

    def score(self, job: JobInput) -> ScoreResult:
        skill, matched, missing = self._skills(job)
        experience = self._experience(job)
        seniority = self._seniority(job)
        location = self._location(job)
        company = self._company(job)
        interview = self._deterministic_interview(skill, experience, seniority)

        result = ScoreResult(
            job_id=job.job_id,
            role_category=job.role_category,
            skill_score=skill,
            experience_score=experience,
            location_score=location,
            seniority_score=seniority,
            company_score=company,
            interview_likelihood=interview,
            matched_skills=matched,
            missing_skills=missing,
            match_score=0,
            priority="LOW",
            input_hash=self.input_hash(job),
            scored_by=SCORED_BY_DETERMINISTIC,
        )
        return self._finalize(job.role_category, result)

    def with_interview(
        self, job_role: str, result: ScoreResult, interview: int, scored_by: str
    ) -> ScoreResult:
        """Return a copy of ``result`` with a new interview likelihood applied."""
        updated = ScoreResult(**{**result.__dict__})
        updated.interview_likelihood = _clamp(interview)
        updated.scored_by = scored_by
        return self._finalize(job_role, updated)

    def _finalize(self, role: str, r: ScoreResult) -> ScoreResult:
        w = self._config.weights
        raw = (
            w.get("skill", 0) * r.skill_score
            + w.get("experience", 0) * r.experience_score
            + w.get("location", 0) * r.location_score
            + w.get("seniority", 0) * r.seniority_score
            + w.get("company", 0) * r.company_score
            + w.get("interview", 0) * r.interview_likelihood
        )
        tier = self._profile.tier_for(role)
        factor = self._config.role_priority_factor.get(tier, 1.0)
        r.match_score = _clamp(raw * factor)
        r.priority = self._priority(r.match_score)
        return r

    def _priority(self, score: int) -> str:
        t = self._config.priority_thresholds
        if score >= t.get("high", 75):
            return "HIGH"
        if score >= t.get("medium", 55):
            return "MEDIUM"
        return "LOW"
