from pipeline.fronthalf.review import (
    FRONT_HALF_REQUIREMENTS,
    first_statement_page,
    front_half_questions,
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


def test_highlights_table_does_not_truncate_front_half():
    # A Strategic-Report financial-highlights table (Change/% columns) on page 4
    # must NOT be read as the start of the primary statements. The real P&L is on
    # page 15. The directors'-report content on pages 5-10 must stay in the front
    # half (regression: FC.pdf reported going concern / responsibilities missing).
    highlights = {
        "rowCount": 1, "columnCount": 8, "cells": [
            {"rowIndex": 0, "columnIndex": i, "content": v} for i, v in enumerate(
                ["", "31 December 2024", "31 December 2023", "Change",
                 "£'000", "£'000", "£'000", "%"])],
        "boundingRegions": [{"pageNumber": 4}]}
    real_pl = {
        "rowCount": 1, "columnCount": 4, "cells": [
            {"rowIndex": 0, "columnIndex": i, "content": v} for i, v in enumerate(
                ["", "Note", "2024", "2023", "Turnover", "gross profit",
                 "operating"])],
        "boundingRegions": [{"pageNumber": 15}]}
    layout = {
        "tables": [highlights, real_pl],
        "paragraphs": [
            {"content": "Directors' responsibilities statement",
             "boundingRegions": [{"pageNumber": 9}]},
            {"content": "the going concern basis of preparation",
             "boundingRegions": [{"pageNumber": 9}]},
        ],
    }
    assert first_statement_page(layout) == 15        # not 4
    fh = gather_front_half(layout)
    assert "Directors' responsibilities statement" in fh
    assert "going concern" in fh


def test_requirements_cover_always_applicable_items():
    refs = {r[1] for r in FRONT_HALF_REQUIREMENTS}
    assert "s418" in refs              # audit information statement (always applies)
    assert "s416(1)(a)" in refs        # directors' names (always applies)
    assert any("Sch7" in r[1] for r in FRONT_HALF_REQUIREMENTS)
    # conditional items are NOT hard requirements (they over-flag) ...
    assert "s416(3)" not in refs       # dividend recommendation
    assert "Sch7 para10" not in refs   # >250-employee disabled-persons policy
    assert "Sch7 para11" not in refs   # >250-employee engagement statement


def test_conditional_items_are_questions_with_citations():
    qs = front_half_questions()
    keys = {q.fact_key for q in qs}
    assert "dividend_recommended" in keys
    assert "average_employees_gt_250" in keys
    # every front-half question carries a lookup citation
    assert all(q.affected_refs and q.affected_refs[0] for q in qs)
    divq = next(q for q in qs if q.fact_key == "dividend_recommended")
    assert "s416(3)" in divq.affected_refs[0]
