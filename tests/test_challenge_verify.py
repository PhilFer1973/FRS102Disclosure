from pipeline.challenge.verify import challenge_missing
from pipeline.engine.checklist import EngineResult, Requirement
from pipeline.engine.presence import PresenceResult


def _pres(ref, status):
    req = Requirement("id-" + ref, "FRS102", ref, "both", f"Disclose {ref}", "always",
                      None, (), "missing", "standard-material")
    return PresenceResult(EngineResult(req, "applicable"), status, "")


class _FakeClient:
    """Refutes the first finding, upholds the second."""
    def complete_json(self, role, system, user, schema, max_tokens=4000):
        return {"results": [{"index": 0, "refuted": True, "evidence": "see note 99"},
                            {"index": 1, "refuted": False, "evidence": ""}]}


def test_challenge_flips_refuted_to_present():
    to_challenge = [_pres("3.9", "absent"), _pres("33.9", "absent")]
    out, refuted = challenge_missing(to_challenge, "narrative", _FakeClient())
    assert refuted == 1
    by_ref = {p.requirement.requirement.reference: p for p in out}
    assert by_ref["3.9"].status == "present"          # refuted -> discarded as a finding
    assert "Challenge located it" in by_ref["3.9"].evidence
    assert by_ref["33.9"].status == "absent"          # upheld -> stays missing
