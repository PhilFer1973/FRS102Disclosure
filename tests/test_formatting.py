from pipeline.validate.formatting import (
    check_cross_references,
    check_formatting,
    check_note_numbering,
)
from pipeline.validate.fs_model import FinancialStatements, LineItem, Statement


def test_note_numbering_gap_and_duplicate():
    findings = check_note_numbering(["1", "2", "4", "5", "5"])
    types = [(f.check_type, f.location) for f in findings]
    assert ("note_numbering", "note 3") in types          # gap
    assert ("note_numbering", "note 5") in types          # duplicate
    # contiguous sequence -> nothing
    assert check_note_numbering(["1", "2", "3"]) == []


def test_letter_suffixed_notes_ignored_for_gaps():
    # 1A should not create phantom gaps
    assert check_note_numbering(["1", "1A", "2"]) == []


def test_broken_cross_reference_detected():
    findings = check_cross_references({"14", "17"}, {"14", "16"})
    assert any("17" in f.location for f in findings)
    assert not any("14" in f.location for f in findings)   # 14 exists


def test_check_formatting_combines():
    bs = Statement("balance_sheet", [
        LineItem("debtors", "Debtors", note_ref="14"),
        LineItem("creditors", "Creditors", note_ref="17"),
    ])
    fs = FinancialStatements("T", "2025-12-31", statements={"balance_sheet": bs})
    findings = check_formatting(fs, present_notes=["13", "14", "16"])
    # note 17 referenced but absent; note 15 gap
    assert any(f.check_type == "cross_reference_note" and "17" in f.location
               for f in findings)
    assert any(f.check_type == "note_numbering" and "15" in f.location
               for f in findings)
