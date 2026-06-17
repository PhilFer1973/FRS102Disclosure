"""Note-number recovery and cross-cast assembly (no LLM: pure helpers)."""

from pipeline.extract.structure import (
    _note_headings,
    _note_number_for,
    note_numbers_present,
)


def test_note_numbers_present_robust_to_title_quirks():
    layout = {"paragraphs": [
        {"content": "6. Operating (loss)/profit"},                  # parentheses
        {"content": "25. . Ultimate parent company"},              # OCR double-period
        {"content": "3. Judgments in applying accounting policies and key "
                    "sources of estimation uncertainty"},          # long title
        {"content": "13. Stocks"},
        {"content": "2.1 Revenue recognition"},                    # sub-item -> excluded
        {"content": "Note 4 is referenced here in prose."},        # not 'N. ' start
    ]}
    nums = note_numbers_present(layout)
    assert {"3", "6", "13", "25"} <= set(nums)
    assert "2" not in nums           # 2.1 sub-item must not register note 2
    assert "4" not in nums           # prose mention must not register note 4
    assert nums == sorted(nums, key=int)


def _para(text, page, y):
    return {"content": text, "boundingRegions": [{"pageNumber": page,
            "polygon": [1, y, 2, y, 2, y + 0.2, 1, y + 0.2]}]}


def _table(page, y):
    return {"boundingRegions": [{"pageNumber": page,
            "polygon": [1, y, 5, y, 5, y + 1, 1, y + 1]}]}


def test_note_headings_parsed():
    layout = {"paragraphs": [
        _para("14. Debtors", 34, 2.0),
        _para("2. Accounting policies (continued)", 25, 1.0),  # continued -> skip
        _para("16. Cash and cash equivalents", 35, 3.0),
        _para("Some narrative paragraph", 34, 5.0),            # not a heading
    ]}
    headings = _note_headings(layout)
    nums = {h["number"] for h in headings}
    assert nums == {"14", "16"}
    assert not any("Accounting" in h["title"] for h in headings)


def test_note_number_for_table_by_position():
    headings = [
        {"number": "13", "title": "Stocks", "page": 34, "top": 1.0},
        {"number": "14", "title": "Debtors", "page": 34, "top": 4.0},
    ]
    # a table below the '14. Debtors' heading on the same page belongs to note 14
    assert _note_number_for(_table(34, 4.5), headings) == "14"
    # a table between the two headings belongs to note 13
    assert _note_number_for(_table(34, 2.0), headings) == "13"
    # a table on a different page matches neither
    assert _note_number_for(_table(99, 1.0), headings) is None
