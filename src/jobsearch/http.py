"""Polite HTTP client: shared headers, per-host rate limiting, retry/backoff."""

from __future__ import annotations

import threading
import time

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from jobsearch.config import Settings


class HttpClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.Client(
            timeout=settings.http_timeout,
            headers={"User-Agent": settings.http_user_agent, "Accept": "application/json"},
            follow_redirects=True,
        )
        self._lock = threading.Lock()
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            wait = self._settings.rate_limit_delay - elapsed
            if wait > 0:
                time.sleep(wait)
            self._last_request_at = time.monotonic()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        reraise=True,
    )
    def get_json(self, url: str, params: dict | None = None) -> dict | list:
        self._throttle()
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
