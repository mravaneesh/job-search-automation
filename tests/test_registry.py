from jobsearch.registry.loader import load_registry


def test_registry_loads_and_validates():
    reg = load_registry()
    assert reg.companies
    assert reg.aggregators

    # Every implemented ATS company must carry a token.
    for c in reg.companies:
        if c.is_implemented and c.source in {"greenhouse", "lever", "ashby"}:
            assert c.token, f"{c.name} is implemented but missing a token"

    # Names are unique (loader raises otherwise, but assert the count too).
    names = [c.name for c in reg.companies]
    assert len(names) == len(set(names))


def test_known_targets_present():
    reg = load_registry()
    names = {c.name for c in reg.companies}
    for expected in ["Google", "Stripe", "Razorpay", "OpenAI", "Databricks"]:
        assert expected in names
