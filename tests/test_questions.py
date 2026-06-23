from cli.next_question import ASKABLE, next_question
from pipeline.engine.checklist import EngineResult, Requirement
from pipeline.engine.questions import undetermined_facts


def _req(ref, facts):
    return Requirement("id-" + ref, "FRS102", ref, "both", "text", "conditional",
                       " AND ".join(f"{f} == true" for f in facts), tuple(facts),
                       "missing", "standard-material")


def test_undetermined_facts_aggregates_provenance():
    results = [
        EngineResult(_req("9.23", ["is_consolidated"]), "undetermined",
                     ("is_consolidated",)),
        EngineResult(_req("9.27", ["is_consolidated"]), "undetermined",
                     ("is_consolidated",)),
        EngineResult(_req("34.40", ["is_retirement_benefit_plan"]), "undetermined",
                     ("is_retirement_benefit_plan",)),
        EngineResult(_req("4.1", []), "applicable"),     # resolved -> ignored
    ]
    prov = undetermined_facts(results)
    # citations are source-qualified so each is directly lookup-able
    assert prov["is_consolidated"] == {"FRS102 9.23", "FRS102 9.27"}
    assert prov["is_retirement_benefit_plan"] == {"FRS102 34.40"}
    assert "FRS102 4.1" not in {r for refs in prov.values() for r in refs}


def test_interview_only_asks_allowlisted_judgement_facts():
    """The interview may ask ONLY genuine reviewer-judgement facts. A material fact
    that should be read/computed from the accounts is never put to the reviewer —
    it is reported as a resolver gap. This is what stops the 'why are you asking me
    something that's in the accounts?' loop."""
    reqs = [_req("X.1", ["not_going_concern"]),   # allowlisted judgement
            _req("X.2", ["is_lessee"])]           # accounts-derivable -> a gap
    assert "not_going_concern" in ASKABLE and "is_lessee" not in ASKABLE

    # drive the whole interview: is_lessee is NEVER asked, always reported as a gap
    answers: dict[str, object] = {}
    asked: list[str] = []
    while True:
        r = next_question({}, answers, [], reqs, "pre-PR2024")
        assert "is_lessee" in r["resolver_gaps"]        # the gap is always surfaced
        if r["done"]:
            break
        fk = r["question"]["fact_key"]
        assert fk in ASKABLE                            # only judgement facts asked
        asked.append(fk)
        answers[fk] = False
    assert "not_going_concern" in asked
    assert "is_lessee" not in asked
