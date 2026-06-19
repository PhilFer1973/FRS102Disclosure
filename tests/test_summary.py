from decimal import Decimal

from pipeline.assemble.summary import build_summary, humanize_money
from pipeline.engine.checklist import EngineResult, Requirement
from pipeline.engine.materiality import Materiality
from pipeline.engine.presence import PresenceResult
from pipeline.engine.questions import Question
from pipeline.validate.checks import Finding


def test_humanize_money():
    assert humanize_money(Decimal(193481)) == "£193k"
    assert humanize_money(Decimal(26350000)) == "£26.4m"
    assert humanize_money(Decimal(500)) == "£500"
    assert humanize_money(None) == "n/a"


def _presence(ref, status):
    req = Requirement("id-" + ref, "FRS102", ref, "missing", "Disclose " + ref,
                      "always", None, (), "missing", "standard-material")
    return PresenceResult(EngineResult(req, "applicable"), status, "")


def test_build_summary_counts_by_category():
    numerical = [
        Finding("judgment", "FRS102 18.22", "goodwill nil amortisation", "standard-material"),
        Finding("cast", "income:gp", "does not cast", "standard-material"),
        Finding("note_numbering", "note 7", "gap", "standard-material"),
    ]
    presence = [_presence("3.17", "absent"), _presence("5.7E", "unclear"),
                _presence("9.1", "present")]      # 'present' excluded
    questions = [Question("is_small_entity", "Is it small?", ("FRS102 1A.1",))]
    mat = Materiality("1% of turnover (loss-making)", Decimal(532))

    s = build_summary("Teneo", "2024-12-31", mat, numerical, presence, questions)
    assert s["counts"]["by_category"] == {
        "judgement": 1, "disclosure": 2, "numerical": 1, "formatting": 1}
    assert s["counts"]["total_findings"] == 5
    assert s["counts"]["need_judgement"] == 1
    assert s["counts"]["questions"] == 1
    assert s["materiality"]["display"] == "£532"
    assert s["entity"] == "Teneo"
    assert len(s["findings"]) == 5            # 3 numerical + 2 non-present disclosure
    assert s["questions"][0]["citation"] == "FRS102 1A.1"
