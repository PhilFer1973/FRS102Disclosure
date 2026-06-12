"""Tests against a fixture of verbatim pages from the real frs102_2022.xml:

- page 5: contents page (bare-id rows, appendix-heading rows)
- page 12: Section 1 heading + opening paragraphs
- pages 68-69: Section 4 heading + body paragraphs, footers, a footnote
- page 348/350: back matter (Appendix IV RoI references quoting 1.10, 22.8)
"""

from pathlib import Path

import pytest

from pipeline.parse_frs102 import _family_ok, parse_file, reconciliation_report

FIXTURE = Path(__file__).parent / "fixtures" / "frs102_2022_extract.xml"
CORPUS_2022 = Path(__file__).parent.parent / "corpus" / "tier1" / "frs102_2022.xml"
CORPUS_2024 = Path(__file__).parent.parent / "corpus" / "tier1" / "frs102_2024.xml"


@pytest.fixture(scope="module")
def result():
    return parse_file(FIXTURE)


def test_edition_mapped(result):
    assert result.edition == "pre-PR2024"


def test_section_4_paragraphs_accepted(result):
    refs = {r.reference for r in result.records}
    assert "4.1" in refs
    assert "4.1A" in refs
    assert "4.2" in refs


def test_paragraph_text_has_id_stripped_and_normalised(result):
    p41 = next(r for r in result.records if r.reference == "4.1")
    assert not p41.text.startswith("4.1")
    assert "  " not in p41.text
    assert "ﬁ" not in p41.text  # ligature normalised


def test_hierarchy_includes_section_title(result):
    p41 = next(r for r in result.records if r.reference == "4.1")
    assert p41.hierarchy[0] == "FRS 102"
    assert p41.hierarchy[1].startswith("Section 4")
    assert "Statement of Financial Position" in p41.hierarchy[1]
    assert p41.hierarchy[-1] == "4.1"


def test_contents_rows_and_footers_excluded_not_lost(result):
    reasons = {e.reason for e in result.excluded}
    assert "contents-row" in reasons
    assert "page-footer" in reasons


def test_back_matter_quotes_rejected(result):
    rejected = [e for e in result.excluded if e.reason == "outside-section-context"]
    rejected_ids = {e.detail for e in rejected}
    assert "22.8" in rejected_ids  # RoI equivalence table on p350, not Section 22
    accepted_22_8 = [r for r in result.records if r.reference == "22.8"]
    assert accepted_22_8 == []  # section 22 pages not in fixture


def test_page_split_paragraph_merged(result):
    """4.4A breaks across pages 69/70; its continuation arrives as a plain
    text-block at the top of page 70 and must be merged back in."""
    p44a = next(r for r in result.records if r.reference == "4.4A")
    assert p44a.text.endswith("notes to the financial statements.")
    assert "4.4A" in result.page_split_merges


def test_reconciliation_identity(result):
    accounted = (
        len(result.records) + len(result.merged_continuations) + len(result.excluded)
    )
    assert accounted == result.numbered_block_count


def test_family_rules():
    assert _family_ok("4", "4")
    assert _family_ok("PBE34", "34")
    assert _family_ok("PBE34B", "34")
    assert _family_ok("1AC", "1A")
    assert _family_ok("2A", "2")
    assert not _family_ok("22", "35")
    assert not _family_ok("34", "3")  # '4' is not an appendix letter
    assert not _family_ok("1AC", "1")


def test_report_renders(result):
    report = reconciliation_report(result, "fixture")
    assert "Accounting identity" in report
    assert "page-footer" in report


@pytest.mark.parametrize(
    ("corpus", "min_records"),
    [(CORPUS_2022, 1300), (CORPUS_2024, 1600)],
    ids=["2022", "2024"],
)
def test_full_corpus_reconciles(corpus, min_records):
    if not corpus.exists():
        pytest.skip("corpus file not present")
    res = parse_file(corpus)
    assert len(res.records) >= min_records
    accounted = len(res.records) + len(res.merged_continuations) + len(res.excluded)
    assert accounted == res.numbered_block_count
    # exactly one record per reference
    refs = [r.reference for r in res.records]
    assert len(refs) == len(set(refs))


def test_periodic_review_signature_in_family_counts():
    """S20 and S23 grew massively in the 2024 edition; S2A became a full section."""
    if not (CORPUS_2022.exists() and CORPUS_2024.exists()):
        pytest.skip("corpus files not present")

    def fam_count(path, fam):
        return sum(
            1 for r in parse_file(path).records if r.reference.partition(".")[0] == fam
        )

    assert fam_count(CORPUS_2024, "23") > 2 * fam_count(CORPUS_2022, "23")
    assert fam_count(CORPUS_2024, "20") > 2 * fam_count(CORPUS_2022, "20")
    assert fam_count(CORPUS_2024, "2A") > fam_count(CORPUS_2022, "2A")
