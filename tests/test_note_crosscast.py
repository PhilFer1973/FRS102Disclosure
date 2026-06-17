"""Note-number recovery and cross-cast assembly (no LLM: pure helpers)."""

from pipeline.extract.structure import _note_headings, _note_number_for


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
