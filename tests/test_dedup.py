from jobsearch.dedup.deduper import fingerprint


def test_seniority_collapses():
    a = fingerprint("Acme", "Senior Backend Engineer", "Bengaluru")
    b = fingerprint("Acme", "Backend Engineer", "Bengaluru")
    assert a == b


def test_punctuation_and_case_insensitive():
    a = fingerprint("Acme, Inc.", "Backend Engineer", "Bengaluru")
    b = fingerprint("acme inc", "backend engineer", "bengaluru")
    assert a == b


def test_different_company_differs():
    a = fingerprint("Acme", "Backend Engineer", "Bengaluru")
    b = fingerprint("Globex", "Backend Engineer", "Bengaluru")
    assert a != b


def test_different_location_differs():
    a = fingerprint("Acme", "Backend Engineer", "Bengaluru")
    b = fingerprint("Acme", "Backend Engineer", "Mumbai")
    assert a != b
