from pipeline.judgment.assess import PROBES, Probe, assess_probe
from pipeline.validate.checks import Finding


class _FakeClient:
    def __init__(self, response):
        self._response = response

    def complete_json(self, role, system, user, schema, max_tokens=1500):
        return self._response


def _no_retrieve(query, edition, k=5, source="FRS102"):
    return [("19.23", "Goodwill shall be amortised over its useful life.")]


def test_finding_only_with_citation(monkeypatch):
    monkeypatch.setattr("pipeline.judgment.assess.retrieve", _no_retrieve)
    probe = PROBES[0]
    # issue found, with citation -> Finding
    client = _FakeClient({"issue_found": True, "finding": "Goodwill not amortised",
                          "citation": "19.23", "confidence": 0.9})
    f = assess_probe(probe, "narrative", "pre-PR2024", client)
    assert isinstance(f, Finding) and f.check_type == "judgment"
    assert "19.23" in f.location

    # issue found but no citation -> no finding (no citation, no finding)
    client = _FakeClient({"issue_found": True, "finding": "x", "citation": " ",
                          "confidence": 0.5})
    assert assess_probe(probe, "narrative", "pre-PR2024", client) is None

    # no issue -> no finding
    client = _FakeClient({"issue_found": False, "finding": "", "citation": "",
                          "confidence": 0.1})
    assert assess_probe(probe, "narrative", "pre-PR2024", client) is None


def test_probes_have_queries():
    assert all(isinstance(p, Probe) and p.query and p.instruction for p in PROBES)
