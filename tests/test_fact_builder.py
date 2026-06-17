from decimal import Decimal

from pipeline.facts.builder import accounts_context
from pipeline.validate.fs_model import FinancialStatements, LineItem, Statement

D = Decimal


def _fs():
    bs = Statement("balance_sheet", [
        LineItem("share_capital", "Called up share capital", D(206541), D(206541)),
        LineItem("net_assets", "Net assets", D(7843774), D(8056962)),
    ])
    return FinancialStatements("Four Communications Limited", "2024-12-31",
                               statements={"balance_sheet": bs})


def test_accounts_context_includes_entity_lines_and_notes():
    ctx = accounts_context(_fs(), ["14. Debtors", "22. Share capital"], "pre-PR2024")
    assert "Four Communications Limited" in ctx
    assert "pre-PR2024" in ctx
    assert "Called up share capital: 206,541" in ctx
    assert "14. Debtors" in ctx
    assert "balance sheet" in ctx  # underscores humanised
