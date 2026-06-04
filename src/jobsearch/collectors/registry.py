"""Map source identifiers to collector classes."""

from __future__ import annotations

from jobsearch.collectors.ashby import AshbyCollector
from jobsearch.collectors.base import Collector
from jobsearch.collectors.career_page import CareerPageCollector
from jobsearch.collectors.greenhouse import GreenhouseCollector
from jobsearch.collectors.indeed import IndeedCollector
from jobsearch.collectors.lever import LeverCollector
from jobsearch.collectors.linkedin import LinkedInCollector
from jobsearch.collectors.naukri import NaukriCollector
from jobsearch.collectors.wellfound import WellfoundCollector

# API / career-page collectors (per company).
COMPANY_COLLECTORS: dict[str, type[Collector]] = {
    "greenhouse": GreenhouseCollector,
    "lever": LeverCollector,
    "ashby": AshbyCollector,
    "career_page": CareerPageCollector,
}

# Playwright aggregator collectors (per role search).
AGGREGATOR_COLLECTORS = {
    "linkedin": LinkedInCollector,
    "indeed": IndeedCollector,
    "naukri": NaukriCollector,
    "wellfound": WellfoundCollector,
}
