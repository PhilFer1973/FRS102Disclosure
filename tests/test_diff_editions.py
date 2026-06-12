from pathlib import Path

import pytest

from pipeline.diff_editions import diff_records, report_markdown, section_summary
from pipeline.records import ParagraphRecord

BUILD = Path(__file__).parent.parent / "build"


def rec(ref, text, edition="pre-PR2024"):
    return ParagraphRecord(source="FRS102", reference=ref, edition=edition,
                           text=text, hierarchy=["FRS 102", ref], location="section_body")


def test_classification():
    old = [rec("4.1", "same text"), rec("4.2", "old wording"), rec("4.3", "gone")]
    new = [rec("4.1", "same text", "PR2024"), rec("4.2", "new wording", "PR2024"),
           rec("4.4", "brand new", "PR2024")]
    entries = {e.reference: e for e in diff_records(old, new)}
    assert entries["4.1"].status == "unchanged"
    assert entries["4.1"].applicability == "both"
    assert entries["4.2"].status == "amended"
    assert 0 < entries["4.2"].similarity < 1
    assert entries["4.3"].status == "deleted"
    assert entries["4.3"].applicability == "pre-PR2024"
    assert entries["4.4"].status == "new"
    assert entries["4.4"].applicability == "PR2024"


def test_section_summary_groups_by_family():
    old = [rec("1AC.1", "a"), rec("4.1", "b")]
    new = [rec("1AC.1", "a", "PR2024")]
    summary = section_summary(diff_records(old, new))
    assert summary["1AC"]["unchanged"] == 1
    assert summary["4"]["deleted"] == 1


def test_report_contains_sanity_section():
    old = [rec("23.1", "x"), rec("20.1", "y")]
    new = [rec("23.1", "x rewritten", "PR2024"), rec("20.1", "y rewritten", "PR2024")]
    report = report_markdown(diff_records(old, new))
    assert "Periodic Review sanity check" in report
    assert "OK" in report


def test_real_diff_shows_periodic_review_changes():
    old_p, new_p = BUILD / "frs102_2022.jsonl", BUILD / "frs102_2024.jsonl"
    if not (old_p.exists() and new_p.exists()):
        pytest.skip("parsed corpus not built")
    from pipeline.records import read_jsonl

    entries = diff_records(read_jsonl(old_p), read_jsonl(new_p))
    summary = section_summary(entries)

    def pct(fam):
        c = summary[fam]
        return (c["amended"] + c["new"] + c["deleted"]) / sum(c.values())

    assert pct("23") >= 0.5  # revenue rewritten
    assert pct("20") >= 0.5  # leases substantially amended
    assert pct("4") <= 0.25  # statement of financial position barely touched
