"""Tests against fixtures of verbatim CLML subtrees from the real files:

- ca06_extract.xml: Part 15 (s411 group, s414 group) + Part 29 (s993) for
  scope-filter testing; NumberOfProvisions patched to the extract count.
- si2008_410_extract.xml: reg 4 group, Sch 1 para 45, Sch 7 paras 1/1A/3.
"""

from pathlib import Path

import pytest

from pipeline.parse_legislation import parse_file, reconciliation_report

FIXTURES = Path(__file__).parent / "fixtures"
CA06_FIXTURE = FIXTURES / "ca06_extract.xml"
SI_FIXTURE = FIXTURES / "si2008_410_extract.xml"
CA06_CORPUS = Path(__file__).parent.parent / "corpus" / "tier1" / "ca06.xml"
SI_CORPUS = Path(__file__).parent.parent / "corpus" / "tier1" / "si2008_410.xml"


def test_ca06_part_filter_and_references():
    res = parse_file(CA06_FIXTURE, part="15")
    refs = {r.reference for r in res.records}
    assert "s411(1)" in refs
    assert "s411(1A)" in refs
    assert "s414(1)" in refs
    # Part 29 (s993) excluded by scope
    assert not any(r.reference.startswith("s993") for r in res.records)
    assert sum(res.skipped_out_of_scope.values()) == 1


def test_ca06_record_content():
    res = parse_file(CA06_FIXTURE, part="15")
    s411_1 = next(r for r in res.records if r.reference == "s411(1)")
    assert "average number of persons employed" in s411_1.text
    assert s411_1.source == "CA06"
    assert s411_1.edition == "both"
    assert s411_1.location == "provision"
    assert any("Part 15" in h for h in s411_1.hierarchy)
    assert s411_1.hierarchy[-1] == "(1)"


def test_ca06_no_part_filter_includes_all():
    res = parse_file(CA06_FIXTURE)
    assert any(r.reference.startswith("s993") for r in res.records)


def test_si_regulation_and_schedule_references():
    res = parse_file(SI_FIXTURE, schedules={"1", "7"})
    refs = {r.reference for r in res.records}
    assert "reg 4(1)" in refs
    assert "Sch 1 para 45" in refs
    assert "Sch 7 para 1" in refs
    sch7_3 = [r for r in refs if r.startswith("Sch 7 para 3(")]
    assert sch7_3  # para 3 has subparagraphs


def test_si_p3_list_markers_keep_parentheses():
    res = parse_file(SI_FIXTURE, schedules={"1", "7"})
    reg41 = next(r for r in res.records if r.reference == "reg 4(1)")
    assert "(a)" in reg41.text
    assert "awhich" not in reg41.text.replace(" ", "")[:60]


def test_si_schedule_scope_filter():
    res = parse_file(SI_FIXTURE, schedules={"7"})
    assert not any(r.reference.startswith("Sch 1") for r in res.records)
    assert "Schedule 1" in res.skipped_out_of_scope


def test_fixture_reconciliation_identity():
    for fixture, kwargs in ((CA06_FIXTURE, {"part": "15"}), (SI_FIXTURE, {})):
        res = parse_file(fixture, **kwargs)
        assert res.p1_seen + res.p1_nested == res.declared_provisions
        report = reconciliation_report(res, fixture.name)
        assert "P1 identity" in report


@pytest.mark.parametrize(
    ("corpus", "kwargs", "expect_in_scope"),
    [
        (CA06_CORPUS, {"part": "15", "schedules": set()}, 121),
        (SI_CORPUS, {"schedules": {"1", "5", "7"}}, 161),
    ],
    ids=["ca06", "si"],
)
def test_full_corpus_reconciles(corpus, kwargs, expect_in_scope):
    if not corpus.exists():
        pytest.skip("corpus file not present")
    res = parse_file(corpus, **kwargs)
    assert res.p1_seen + res.p1_nested == res.declared_provisions
    assert res.p1_in_scope == expect_in_scope
    assert len(res.records) > expect_in_scope  # subsections multiply records
