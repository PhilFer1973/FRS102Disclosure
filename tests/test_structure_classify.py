from pipeline.extract.structure import classify_table


def _table(*cell_texts):
    return {"cells": [{"content": t} for t in cell_texts]}


def test_classic_balance_sheet_with_net_assets():
    assert classify_table(_table("Fixed assets", "Net assets", "Capital")) == "balance_sheet"


def test_older_style_balance_sheet_shareholders_funds():
    # Teneo-style: 'Shareholders' funds' rather than 'Net assets', subtotal wrapped
    t = _table("Fixed assets", "Current assets", "Net current assets",
               "Total assets less current\nliabilities", "Shareholders' funds")
    assert classify_table(t) == "balance_sheet"


def test_statement_of_changes_in_equity_is_not_a_balance_sheet():
    # SOCE: share capital / premium / P&L reserve / total equity, no fixed assets
    t = _table("Share capital", "Share premium account", "Profit and loss account",
               "Total equity", "Dividends paid", "1 January 2024")
    assert classify_table(t) is None


def test_income_statement():
    assert classify_table(_table("Turnover", "Operating profit", "2024")) == "income"
