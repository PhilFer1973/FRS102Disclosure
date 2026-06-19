from pipeline.extract.tables import extract_statement


def _table(rows):
    """rows: list of row-lists of cell strings -> Azure-style table dict."""
    cells = []
    for ri, row in enumerate(rows):
        for ci, text in enumerate(row):
            cells.append({"rowIndex": ri, "columnIndex": ci, "content": text})
    return {"cells": cells, "rowCount": len(rows),
            "columnCount": max(len(r) for r in rows)}


def test_notes_header_column_is_excluded():
    # Teneo layout: header 'Notes' (plural), a note-reference column of single
    # digits, then current and prior money columns. The note digits must NOT be
    # read as figures (regression: turnover was read as 4 instead of 53,209).
    t = _table([
        ["", "Notes", "2024", "2023"],
        ["", "", "£'000", "£'000"],
        ["Turnover", "4", "53,209", "44,584"],
        ["Cost of sales", "", "(16,626)", "(14,131)"],
        ["Gross profit", "", "36,583", "30,453"],
        ["Operating loss", "7", "(1,867)", "(349)"],
    ])
    rows = {r.label: r for r in extract_statement(t)}
    assert rows["Turnover"].current == 53209
    assert rows["Turnover"].prior == 44584
    assert rows["Turnover"].note == "4"
    # the cast turnover + cost of sales = gross profit now holds
    assert rows["Turnover"].current + rows["Cost of sales"].current == \
        rows["Gross profit"].current
    assert rows["Operating loss"].current == -1867


def test_note_singular_header_still_works():
    t = _table([
        ["", "Note", "2024", "2023"],
        ["Turnover", "4", "1,000", "900"],
    ])
    row = extract_statement(t)[0]
    assert (row.current, row.prior, row.note) == (1000, 900, "4")
