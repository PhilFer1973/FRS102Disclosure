from pipeline.fronthalf.review import (
    FRONT_HALF_REQUIREMENTS,
    first_statement_page,
    gather_front_half,
)


def _table(page):
    return {"rowCount": 1, "columnCount": 1,
            "cells": [{"rowIndex": 0, "columnIndex": 0, "content": "Turnover"}],
            "boundingRegions": [{"pageNumber": page}]}


def test_first_statement_page_and_front_half_text():
    # an income table on page 15; front half = pages before it
    layout = {
        "tables": [
            {"rowCount": 1, "columnCount": 1, "cells": [
                {"rowIndex": 0, "columnIndex": 0, "content": "Turnover gross profit operating"}],
             "boundingRegions": [{"pageNumber": 15}]},
        ],
        "paragraphs": [
            {"content": "Directors' report", "boundingRegions": [{"pageNumber": 2}]},
            {"content": "The directors present their report.",
             "boundingRegions": [{"pageNumber": 2}]},
            {"content": "Profit and loss account",
             "boundingRegions": [{"pageNumber": 15}]},   # in the statements, excluded
        ],
    }
    assert first_statement_page(layout) == 15
    fh = gather_front_half(layout)
    assert "Directors' report" in fh
    assert "Profit and loss account" not in fh   # page 15 excluded


def test_requirements_cover_key_statutory_items():
    refs = {r[1] for r in FRONT_HALF_REQUIREMENTS}
    assert "s416(3)" in refs           # dividends
    assert "s418" in refs              # audit information statement
    assert any("Sch7" in r[1] for r in FRONT_HALF_REQUIREMENTS)
