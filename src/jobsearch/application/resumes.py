"""Master-resume library: deterministic selection and tailoring suggestions.

No LLM. Selection is by role match + skill overlap; suggestions are templated
from the job's matched/missing skills. The full resume is never rewritten.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from jobsearch.application.config import ResumeSpec
from jobsearch.application.models import JobContext
from jobsearch.config import CONFIG_DIR


def _lower_set(items) -> set[str]:
    return {str(i).lower() for i in items}


class ResumeLibrary:
    def __init__(self, resumes: list[ResumeSpec]):
        self._resumes = resumes

    @property
    def resumes(self) -> list[ResumeSpec]:
        return list(self._resumes)

    @classmethod
    def from_config(cls, path: Path | None = None) -> ResumeLibrary:
        data = yaml.safe_load((path or CONFIG_DIR / "resumes.yaml").read_text()) or {}
        resumes = [
            ResumeSpec(
                role_category=r["role_category"],
                name=r["name"],
                version=int(r.get("version", 1)),
                focus_skills=list(r.get("focus_skills") or []),
                themes=list(r.get("themes") or []),
                file_path=r.get("file_path"),
                notes=r.get("notes"),
            )
            for r in (data.get("resumes") or [])
        ]
        return cls(resumes)

    def _fit(self, resume: ResumeSpec, job: JobContext) -> float:
        role_bonus = 100 if resume.role_category == job.role_category else 0
        focus = _lower_set(resume.focus_skills)
        job_skills = _lower_set(job.matched_skills) | _lower_set(job.missing_skills)
        overlap = len(focus & job_skills)
        # Prefer the role-matched resume; break ties on skill overlap, then version.
        return role_bonus + overlap * 5 + resume.version * 0.1

    def select_best(self, job: JobContext) -> tuple[ResumeSpec | None, str]:
        if not self._resumes:
            return None, "No resumes configured."
        best = max(self._resumes, key=lambda r: self._fit(r, job))
        if best.role_category == job.role_category:
            reason = f"Role match: '{best.name}' resume targets {job.role_category} roles."
        else:
            reason = (
                f"No exact-role resume; '{best.name}' has the strongest skill overlap "
                f"for this {job.role_category} role."
            )
        return best, reason

    def recommendations(self, resume: ResumeSpec | None, job: JobContext) -> list[str]:
        if resume is None:
            return []
        recs: list[str] = []
        if resume.themes:
            recs.append(
                f"Lead with your {', '.join(resume.themes[:4])} experience — it aligns "
                f"with this {job.role_category} role."
            )
        focus = _lower_set(resume.focus_skills)
        emphasise = [s for s in job.matched_skills if s.lower() in focus]
        if emphasise:
            recs.append(
                f"Emphasise {', '.join(emphasise)} near the top — the role asks for them "
                "and they are resume strengths."
            )
        if job.missing_skills:
            recs.append(
                f"Add concrete evidence of {', '.join(job.missing_skills[:3])} if you have any — "
                "the role lists these but they are not on this resume."
            )
        if not recs:
            recs.append("Resume is well aligned; no targeted changes needed.")
        return recs

    def bullet_suggestions(self, job: JobContext, count: int) -> list[str]:
        """Templated, role-aware bullet starters referencing real matched skills."""
        bullets: list[str] = []
        matched = job.matched_skills or []
        for skill in matched[:count]:
            bullets.append(
                f"Delivered a {job.role_category.replace('_', '/')} feature using {skill}, "
                "quantifying impact (e.g. latency, adoption, or reliability)."
            )
        for skill in job.missing_skills[: max(0, count - len(bullets))]:
            bullets.append(
                f"If applicable, add a bullet showing exposure to {skill} "
                "(side project, course, or production work)."
            )
        while len(bullets) < count:
            bullets.append(
                f"Highlight an outcome relevant to {job.company_name} "
                f"({job.title}) with a measurable result."
            )
        return bullets[:count]
