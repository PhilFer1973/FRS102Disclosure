from pipeline.assemble.delta import compute_delta, summarise


def _f(key, reasoning="x"):
    return {"identity_key": key, "reasoning": reasoning}


def test_new_unchanged_resolved():
    prior = [_f("a"), _f("b")]
    current = [_f("b"), _f("c")]
    items = {it.identity_key: it.status for it in compute_delta(current, prior)}
    assert items == {"b": "unchanged", "c": "new", "a": "resolved"}


def test_regressed_when_previously_resolved():
    prior = []                      # absent in the immediately prior run
    current = [_f("a")]
    items = compute_delta(current, prior, resolved_keys={"a"})
    assert items[0].status == "regressed"
    # without the resolved history, the same finding is just 'new'
    assert compute_delta(current, prior)[0].status == "new"


def test_summarise_counts():
    prior = [_f("a"), _f("b"), _f("c")]
    current = [_f("a"), _f("d")]    # a unchanged, d new, b+c resolved
    counts = summarise(compute_delta(current, prior))
    assert counts == {"new": 1, "unchanged": 1, "resolved": 2, "regressed": 0}
