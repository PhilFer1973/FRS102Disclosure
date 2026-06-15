"""Numerical validation gate tests, on synthetic FS-model fixtures (clean +
seeded defects). No documents or LLM involved — pure deterministic checks."""

from decimal import Decimal

from pipeline.validate.checks import (
    check_casting,
    check_comparatives,
    check_equalities,
    validate,
)
from pipeline.validate.fs_model import (
    Equality,
    FinancialStatements,
    LineItem,
    Note,
    Statement,
)

D = Decimal


def line(id_, label, cur, prior, deriv=None, note=None):
    return LineItem(id=id_, label=label,
                    current=None if cur is None else D(cur),
                    prior=None if prior is None else D(prior),
                    derivation=deriv, note_ref=note)


def clean_fs() -> FinancialStatements:
    """A small but internally consistent set of accounts (in £'000)."""
    bs = Statement("balance_sheet", [
        line("fixed_assets", "Fixed assets", 800, 700),
        line("debtors", "Debtors", 300, 250, note="5"),
        line("cash", "Cash at bank", 200, 150),
        line("current_assets", "Current assets", 500, 400,
             deriv=(("debtors", 1), ("cash", 1))),
        line("creditors", "Creditors", -300, -250),
        line("net_assets", "Net assets", 1000, 850,
             deriv=(("fixed_assets", 1), ("current_assets", 1), ("creditors", 1))),
        line("share_capital", "Called up share capital", 100, 100),
        line("retained", "Retained earnings", 900, 750),
        line("total_equity", "Total equity", 1000, 850,
             deriv=(("share_capital", 1), ("retained", 1))),
    ])
    income = Statement("income", [
        line("profit", "Profit for the year", 200, 180),
    ])
    socie = Statement("socie", [
        line("opening_equity", "Equity b/f", 850, 720),
        line("profit_socie", "Profit for the year", 200, 180),
        line("dividends", "Dividends", -50, -50),
        line("closing_equity", "Equity c/f", 1000, 850,
             deriv=(("opening_equity", 1), ("profit_socie", 1), ("dividends", 1))),
    ])
    notes = {
        "5": Note("5", "Debtors", [
            line("trade", "Trade debtors", 250, 210),
            line("prepay", "Prepayments", 50, 40),
            line("total", "Total debtors", 300, 250,
                 deriv=(("trade", 1), ("prepay", 1))),
        ]),
    }
    eqs = [
        Equality("statement:balance_sheet:net_assets",
                 "statement:balance_sheet:total_equity",
                 "Balance sheet balances (net assets = total equity)"),
        Equality("note:5:total", "statement:balance_sheet:debtors",
                 "Debtors note casts to balance sheet"),
        Equality("statement:socie:closing_equity",
                 "statement:balance_sheet:total_equity",
                 "SoCIE closing equity = balance sheet equity"),
        Equality("statement:socie:profit_socie", "statement:income:profit",
                 "SoCIE profit = income statement profit"),
    ]
    return FinancialStatements(
        entity_name="Test Ltd", period_end="2025-12-31", rounding_unit=D(1),
        statements={"balance_sheet": bs, "income": income, "socie": socie},
        notes=notes, equalities=eqs)


def test_clean_accounts_produce_no_findings():
    assert validate(clean_fs()) == []


def test_broken_cast_detected():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    # corrupt the debtors+cash subtotal
    bs.items = [it if it.id != "current_assets"
                else LineItem("current_assets", "Current assets", D(999), D(400),
                              derivation=(("debtors", 1), ("cash", 1)))
                for it in bs.items]
    findings = check_casting(fs)
    assert any(f.check_type == "cast" and "current_assets" in f.location
               for f in findings)


def test_unbalanced_balance_sheet_detected():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    bs.items = [it if it.id != "retained"
                else LineItem("retained", "Retained earnings", D(950), D(750))
                for it in bs.items]
    findings = check_equalities(fs)
    # total_equity now casts to 1050 vs net_assets 1000
    assert any(f.check_type == "cross_reference"
               and "balances" in f.description.lower() for f in findings) \
        or any(f.check_type == "cast" for f in check_casting(fs))


def test_note_not_crosscasting_to_face_detected():
    fs = clean_fs()
    note = fs.notes["5"]
    note.items = [it if it.id != "total"
                  else LineItem("total", "Total debtors", D(310), D(250),
                                derivation=(("trade", 1), ("prepay", 1)))
                  for it in note.items]
    # note total (310) no longer matches face debtors (300); also breaks its own cast
    findings = validate(fs)
    assert any(f.check_type in ("cross_reference", "cast") for f in findings)


def test_missing_comparative_detected():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    bs.items = [it if it.id != "fixed_assets"
                else LineItem("fixed_assets", "Fixed assets", D(800), None)
                for it in bs.items]
    findings = check_comparatives(fs)
    assert any(f.check_type == "comparative" and "fixed_assets" in f.location
               for f in findings)


def test_missing_value_is_error_not_silent_zero():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    # remove cash's current value; current_assets derivation can't be evaluated
    bs.items = [it if it.id != "cash"
                else LineItem("cash", "Cash at bank", None, D(150))
                for it in bs.items]
    findings = check_casting(fs)
    errs = [f for f in findings if f.is_error and "current_assets" in f.location]
    assert errs and "no current value" in errs[0].description


def test_broken_equality_reference_is_error():
    fs = clean_fs()
    fs.equalities.append(Equality("statement:balance_sheet:nonexistent",
                                  "statement:balance_sheet:net_assets",
                                  "bad ref check"))
    findings = check_equalities(fs)
    assert any(f.is_error and "does not resolve" in f.description for f in findings)


def test_tolerance_absorbs_rounding_noise():
    fs = clean_fs()
    fs.rounding_unit = D(1)
    bs = fs.statements["balance_sheet"]
    # net_assets off by 1 unit (rounding) across a 3-component sum -> within tol
    bs.items = [it if it.id != "net_assets"
                else LineItem("net_assets", "Net assets", D(1001), D(850),
                              derivation=(("fixed_assets", 1), ("current_assets", 1),
                                          ("creditors", 1)))
                for it in bs.items]
    casts = [f for f in check_casting(fs) if f.check_type == "cast"]
    assert casts == []  # 1-unit drift on a 3-line cast is tolerated
