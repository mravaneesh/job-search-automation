import pytest

from jobsearch.application.config import CompanyTiers
from jobsearch.application.salary import extract_salary, parse_salary_text


@pytest.fixture(scope="module")
def tiers():
    return CompanyTiers.from_config()


def test_tier_resolution(tiers):
    assert tiers.tier_for("Google") == "tier1"
    assert tiers.tier_for("google") == "tier1"  # case-insensitive
    assert tiers.tier_for("Adobe") == "tier2"
    assert tiers.tier_for("Razorpay") == "tier3"  # default
    assert tiers.tier_for(None) == "tier3"
    assert tiers.label("tier1") == "Tier 1"


def test_salary_range_with_currency():
    s = parse_salary_text("Compensation: $150,000 - $200,000 per year")
    assert s.salary_min == 150000
    assert s.salary_max == 200000
    assert s.currency == "USD"
    assert s.found


def test_salary_k_suffix_no_currency():
    s = parse_salary_text("Pay band 120k - 160k")
    assert s.salary_min == 120000
    assert s.salary_max == 160000
    assert s.currency is None


def test_salary_indian_single():
    s = parse_salary_text("CTC ₹25,00,000")
    assert s.salary_min == 2500000
    assert s.currency == "INR"


def test_no_salary_is_safe():
    s = parse_salary_text("Great team, no comp listed")
    assert not s.found
    assert s.salary_min is None


def test_extract_prefers_structured():
    raw = {"salaryRange": {"min": 100000, "max": 140000, "currency": "USD"}}
    s = extract_salary(raw, "ignored $1 - $2 text")
    assert s.salary_min == 100000
    assert s.salary_max == 140000
    assert s.source == "structured"


def test_extract_never_raises_on_garbage():
    assert extract_salary(None, None).found is False
    assert extract_salary({"salaryRange": "weird"}, None).found is False
