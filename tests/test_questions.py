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
    assert prov["is_consolidated"] == {"9.23", "9.27"}
    assert prov["is_retirement_benefit_plan"] == {"34.40"}
    assert "4.1" not in {r for refs in prov.values() for r in refs}
