from decimal import Decimal

from pipeline.extract.tables import extract_statement, parse_money

D = Decimal


def test_parse_money():
    assert parse_money("19,348,055") == D(19348055)
    assert parse_money("(6,567,408)") == D(-6567408)
    assert parse_money("£1,234") == D(1234)
    assert parse_money("-") == D(0)
    assert parse_money("") is None
    assert parse_money(None) is None
    assert parse_money("Turnover") is None
    assert parse_money("46,599") == D(46599)


def _cell(r, c, content):
    return {"rowIndex": r, "columnIndex": c, "content": content}


def _table(rows, cc):
    cells = []
    for r, row in enumerate(rows):
        for c, content in enumerate(row):
            if content:
                cells.append(_cell(r, c, content))
    return {"rowCount": len(rows), "columnCount": cc, "cells": cells,
            "boundingRegions": [{"pageNumber": 1}]}


def test_extract_pl_like_table():
    # label | note | 2024 | 2023
    t = _table([
        ["", "Note", "2024", "2023"],
        ["", "", "£", "£"],
        ["Turnover", "4", "19,348,055", "22,219,434"],
        ["Cost of sales", "", "(6,567,408)", "(6,014,439)"],
        ["Gross profit", "", "12,780,647", "16,204,995"],
    ], cc=4)
    rows = extract_statement(t)
    labels = [r.label for r in rows]
    assert labels == ["Turnover", "Cost of sales", "Gross profit"]
    assert rows[0].note == "4"
    assert rows[0].current == D(19348055) and rows[0].prior == D(22219434)
    assert rows[1].current == D(-6567408)
    # year header row not treated as data
    assert all(r.label not in ("2024", "") for r in rows)


def test_extract_balance_sheet_inner_outer_columns():
    # 6-col vertical format: figures land in different columns but read
    # current-then-prior left to right; blank-label subtotals kept.
    t = _table([
        ["", "Note", "", "2024", "", "2023"],
        ["", "", "", "£", "", "£"],
        ["Stocks", "13", "161,792", "", "349,054", ""],
        ["Debtors", "14", "9,659,187", "", "7,888,837", ""],
        ["", "", "10,847,718", "", "10,367,972", ""],
        ["Net assets", "", "", "7,843,774", "", "8,056,962"],
    ], cc=6)
    rows = extract_statement(t)
    stocks = next(r for r in rows if r.label == "Stocks")
    assert stocks.current == D(161792) and stocks.prior == D(349054)
    subtotal = next(r for r in rows if r.label == "" and r.current == D(10847718))
    assert subtotal.prior == D(10367972)
    na = next(r for r in rows if r.label == "Net assets")
    assert na.current == D(7843774) and na.prior == D(8056962)
