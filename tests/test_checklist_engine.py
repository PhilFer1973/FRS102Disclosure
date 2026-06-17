from pipeline.engine.checklist import (
    Requirement,
    applies_to_edition,
    evaluate_requirement,
    required_facts,
    run_checklist,
)


def req(**kw) -> Requirement:
    base = dict(id="1", source="FRS102", reference="4.12", edition="both",
                requirement_text="Disclose share capital", trigger_type="conditional",
                trigger_condition="has_share_capital == true",
                trigger_facts=("has_share_capital",), direction="missing",
                severity="standard-material")
    base.update(kw)
    return Requirement(**base)


def test_always_is_applicable():
    r = evaluate_requirement(req(trigger_type="always", trigger_condition=None), {})
    assert r.outcome == "applicable"


def test_conditional_fires():
    assert evaluate_requirement(req(), {"has_share_capital": True}).outcome == "applicable"
    assert evaluate_requirement(req(), {"has_share_capital": False}).outcome \
        == "not_applicable"


def test_conditional_undetermined_lists_missing_facts():
    r = evaluate_requirement(req(), {})
    assert r.outcome == "undetermined"
    assert r.missing_facts == ("has_share_capital",)


def test_encouraged_is_separate():
    assert evaluate_requirement(req(trigger_type="encouraged"), {}).outcome \
        == "encouraged"


def test_edition_filter():
    assert applies_to_edition("both", "PR2024")
    assert applies_to_edition("PR2024", "PR2024")
    assert not applies_to_edition("pre-PR2024", "PR2024")
    rules = [req(edition="PR2024"), req(edition="pre-PR2024"), req(edition="both")]
    results = run_checklist(rules, {"has_share_capital": True}, "PR2024")
    assert len(results) == 2  # PR2024 + both, not pre-PR2024


def test_required_facts_worklist():
    rules = [req(trigger_condition="a == true AND b == false",
                 trigger_facts=("a", "b")),
             req(trigger_type="always", trigger_condition=None),
             req(edition="pre-PR2024", trigger_condition="c == true")]
    assert required_facts(rules, "PR2024") == {"a", "b"}  # not c (wrong edition)
