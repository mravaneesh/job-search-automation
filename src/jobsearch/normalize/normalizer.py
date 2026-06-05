"""Turn a RawJob into a normalized Job (or drop it).

Every step here is deterministic. A posting is dropped (returns ``None``) when
it does not match one of the three target roles.
"""

from __future__ import annotations

import re

from jobsearch.dedup.deduper import fingerprint
from jobsearch.models import Job, RawJob
from jobsearch.normalize.locations import LocationFilter
from jobsearch.normalize.roles import RoleClassifier
from jobsearch.normalize.seniority import SeniorityFilter
from jobsearch.normalize.skills import SkillExtractor
from jobsearch.normalize.text import html_to_text

# Lower value = higher priority when the same fingerprint arrives from
# multiple sources (matches the priority order in the task spec).
SOURCE_PRIORITY = {
    "career_page": 10,
    "greenhouse": 20,
    "lever": 30,
    "ashby": 40,
    "wellfound": 50,
    "linkedin": 60,
    "indeed": 70,
    "naukri": 80,
}

_YEARS = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:(?:-|to|–|—)\s*\d{1,2}\s*)?(?:years?|yrs?)", re.IGNORECASE
)
_SENIORITY = [
    ("intern", "Internship"),
    ("principal", "Principal"),
    ("staff", "Staff"),
    ("senior", "Senior"),
    ("lead", "Lead"),
    ("junior", "Junior"),
    ("entry level", "Entry level"),
    ("new grad", "Entry level"),
]


def parse_experience(title: str, description: str | None) -> str | None:
    """Best-effort, deterministic experience extraction.

    Prefers an explicit "N+ years" signal; otherwise falls back to a seniority
    keyword found in the title. Returns None when nothing is found.
    """
    haystacks = [title or ""]
    if description:
        haystacks.append(description)
    for text in haystacks:
        m = _YEARS.search(text)
        if m:
            return f"{m.group(1)}+ years"
    title_l = (title or "").lower()
    for needle, label in _SENIORITY:
        if needle in title_l:
            return label
    return None


class Normalizer:
    def __init__(
        self,
        classifier: RoleClassifier,
        skills: SkillExtractor,
        location_filter: LocationFilter | None = None,
        seniority_filter: SeniorityFilter | None = None,
    ):
        self._classifier = classifier
        self._skills = skills
        self._locations = location_filter or LocationFilter.from_config()
        self._seniority = seniority_filter or SeniorityFilter.from_config()

    @classmethod
    def default(cls) -> Normalizer:
        return cls(
            RoleClassifier.from_config(),
            SkillExtractor.from_config(),
            LocationFilter.from_config(),
            SeniorityFilter.from_config(),
        )

    def normalize(self, raw: RawJob) -> Job | None:
        description = raw.description_text or html_to_text(raw.description_html)

        role = self._classifier.classify(raw.title, description)
        if role is None:
            return None

        # India-or-remote policy (config/locations.yaml): drop foreign on-site.
        if not self._locations.keep(raw.location):
            return None

        # Seniority policy (config/experience.yaml): drop over-level roles.
        if not self._seniority.keep(raw.title, description):
            return None

        skills = self._skills.extract(description)
        experience = parse_experience(raw.title, description)
        fp = fingerprint(raw.company_name, raw.title, raw.location)

        return Job(
            company_name=raw.company_name,
            role_category=role,
            title=raw.title.strip(),
            source=raw.source,
            source_priority=SOURCE_PRIORITY.get(raw.source, 100),
            source_job_id=raw.source_job_id,
            url=raw.url,
            location=raw.location,
            experience=experience,
            employment_type=raw.employment_type,
            description=description,
            skills=skills,
            created_date=raw.created_date,
            fingerprint=fp,
            raw=raw.raw,
        )
