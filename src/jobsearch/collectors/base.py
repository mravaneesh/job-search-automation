"""Collector interface.

A collector is responsible for ONE source. It performs deterministic
extraction only — fetch structured data (preferably JSON), map fields, and
yield RawJob objects. No interpretation, no LLM, no field guessing.

Parsing is deliberately separated from fetching: every collector exposes a
pure ``parse(payload, company_name)`` classmethod/staticmethod that turns an
already-fetched payload into RawJobs. This is what unit tests target, with no
network or browser required.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable

from jobsearch.http import HttpClient
from jobsearch.models import RawJob
from jobsearch.registry.loader import CompanyTarget


class Collector(abc.ABC):
    #: source identifier stored on each job, e.g. "greenhouse"
    source: str

    def __init__(self, http: HttpClient):
        self._http = http

    @abc.abstractmethod
    def collect(self, company: CompanyTarget) -> Iterable[RawJob]:
        """Fetch and yield RawJob objects for a company."""
        raise NotImplementedError
