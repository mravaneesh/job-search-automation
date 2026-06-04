"""Deterministic salary extraction from stored structured data and text.

Reads from the job's ``raw`` payload (ATS-specific fields) and, as a fallback,
a salary phrase in plain text. Always returns a result object; never raises.
No LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Currency symbols / codes -> ISO-ish code.
_CURRENCY = {
    "$": "USD",
    "₹": "INR",
    "£": "GBP",
    "€": "EUR",
    "usd": "USD",
    "inr": "INR",
    "gbp": "GBP",
    "eur": "EUR",
    "rs": "INR",
}

# e.g. "$150,000 - $200,000", "₹25,00,000", "120k–160k", "USD 120000 to 160000"
_RANGE = re.compile(
    r"(?P<cur>[$₹£€]|usd|inr|gbp|eur|rs)?\s?"
    r"(?P<lo>\d[\d,]*\.?\d*)\s?(?P<lok>k|m)?"
    r"\s*(?:-|–|—|to)\s*"
    r"(?P<cur2>[$₹£€]|usd|inr|gbp|eur|rs)?\s?"
    r"(?P<hi>\d[\d,]*\.?\d*)\s?(?P<hik>k|m)?",
    re.IGNORECASE,
)
_SINGLE = re.compile(
    r"(?P<cur>[$₹£€]|usd|inr|gbp|eur|rs)\s?(?P<v>\d[\d,]*\.?\d*)\s?(?P<k>k|m)?",
    re.IGNORECASE,
)


@dataclass
class Salary:
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    source: str | None = None

    @property
    def found(self) -> bool:
        return self.salary_min is not None or self.salary_max is not None


def _num(value: str, suffix: str | None) -> float:
    n = float(value.replace(",", ""))
    if suffix:
        n *= 1000 if suffix.lower() == "k" else 1_000_000
    return n


def _currency(*tokens: str | None) -> str | None:
    for t in tokens:
        if t:
            code = _CURRENCY.get(t.lower())
            if code:
                return code
    return None


def parse_salary_text(text: str | None, source: str = "description") -> Salary:
    if not text:
        return Salary()
    m = _RANGE.search(text)
    if m:
        return Salary(
            salary_min=_num(m.group("lo"), m.group("lok")),
            salary_max=_num(m.group("hi"), m.group("hik")),
            currency=_currency(m.group("cur"), m.group("cur2")),
            source=source,
        )
    m = _SINGLE.search(text)
    if m:
        val = _num(m.group("v"), m.group("k"))
        return Salary(
            salary_min=val, salary_max=val, currency=_currency(m.group("cur")), source=source
        )
    return Salary()


def _from_structured(raw: dict) -> Salary:
    """Pull salary from known ATS fields when present."""
    # Greenhouse pay ranges (when surfaced) and Lever 'salaryRange'.
    pay = raw.get("salaryRange") or raw.get("pay_range") or {}
    if isinstance(pay, dict) and (pay.get("min") or pay.get("max")):
        return Salary(
            salary_min=_safe_float(pay.get("min")),
            salary_max=_safe_float(pay.get("max")),
            currency=pay.get("currency"),
            source="structured",
        )
    # Ashby compensation (includeCompensation=true) — best-effort.
    comp = raw.get("compensation") or {}
    summary = comp.get("compensationTierSummary") if isinstance(comp, dict) else None
    if summary:
        s = parse_salary_text(summary, source="structured")
        if s.found:
            return s
    return Salary()


def _safe_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def extract_salary(raw: dict | None, description: str | None) -> Salary:
    """Best-effort salary extraction. Structured fields win over free text."""
    raw = raw or {}
    structured = _from_structured(raw)
    if structured.found:
        return structured
    return parse_salary_text(description, source="description")
