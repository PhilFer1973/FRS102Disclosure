"""Numerical validation gate tests, on synthetic FS-model fixtures (clean +
seeded defects). No documents or LLM involved — pure deterministic checks."""

from decimal import Decimal

from pipeline.validate.checks import (
    check_casting,
    check_comparatives,
    check_equalities,
    check_ratios,
    validate,
)
from pipeline.validate.fs_model import (
    Equality,
    FinancialStatements,
    LineItem,
    Note,
    RatioCheck,
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


def test_single_new_line_item_not_flagged_as_missing_comparative():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    # one genuinely new line (no prior) must NOT raise a comparative finding
    bs.items = [it if it.id != "fixed_assets"
                else LineItem("fixed_assets", "Fixed assets", D(800), None)
                for it in bs.items]
    assert check_comparatives(fs) == []


def test_wholesale_missing_comparative_column_detected():
    fs = clean_fs()
    bs = fs.statements["balance_sheet"]
    bs.items = [LineItem(it.id, it.label, it.current, None, it.derivation)
                for it in bs.items]  # strip the entire prior column
    findings = check_comparatives(fs)
    assert any(f.check_type == "comparative" and "balance_sheet" in f.location
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


def _tax_note(charge_at_rate):
    """ETR reconciliation note: tax at standard rate + adjustments = total charge,
    and tax at standard rate = PBT x rate."""
    note = Note("8", "Tax", [
        line("pbt", "Profit before tax", 1000, 900),
        line("at_rate", "Tax at standard rate of 25%", charge_at_rate, 225),
        line("disallowed", "Expenses not deductible", 30, 20),
        line("total_tax", "Total tax charge", charge_at_rate + 30, 245,
             deriv=(("at_rate", 1), ("disallowed", 1))),
    ])
    fs = FinancialStatements("T", "2025-12-31", rounding_unit=D(1),
                             notes={"8": note})
    fs.ratio_checks.append(RatioCheck("note:8:at_rate", "note:8:pbt", D("0.25"),
                                      "Tax at standard rate = PBT x 25%"))
    return fs


def test_etr_ratio_passes_when_consistent():
    assert check_ratios(_tax_note(D(250))) == []   # 1000 x 0.25 = 250


def test_etr_ratio_fails_when_standard_rate_line_wrong():
    findings = check_ratios(_tax_note(D(300)))     # 300 != 1000 x 0.25
    assert any(f.check_type == "ratio" for f in findings)


def test_tax_note_reconciliation_via_derivation():
    # tax at standard rate (250) + disallowed (30) = total charge (280): casts
    assert [f for f in check_casting(_tax_note(D(250))) if f.check_type == "cast"] == []
    # break the total charge -> derivation catches it
    fs = _tax_note(D(250))
    note = fs.notes["8"]
    note.items = [it if it.id != "total_tax"
                  else LineItem("total_tax", "Total tax charge", D(999), D(245),
                                derivation=(("at_rate", 1), ("disallowed", 1)))
                  for it in note.items]
    assert any(f.check_type == "cast" for f in check_casting(fs))


def test_fixed_asset_movement_table_rolls():
    """opening + additions - disposals - depreciation = closing, via derivation."""
    note = Note("9", "Tangible fixed assets", [
        line("opening", "Cost b/f", 1000, 900),
        line("additions", "Additions", 200, 150),
        line("disposals", "Disposals", -50, -50),
        line("closing", "Cost c/f", 1150, 1000,
             deriv=(("opening", 1), ("additions", 1), ("disposals", 1))),
    ])
    fs = FinancialStatements("T", "2025-12-31", rounding_unit=D(1), notes={"9": note})
    assert [f for f in check_casting(fs) if f.check_type == "cast"] == []
    # break the roll
    note.items = [it if it.id != "closing"
                  else LineItem("closing", "Cost c/f", D(1200), D(1000),
                                derivation=(("opening", 1), ("additions", 1),
                                            ("disposals", 1)))
                  for it in note.items]
    assert any(f.check_type == "cast" and "closing" in f.location
               for f in check_casting(fs))


def test_ocr_misread_localised_in_cast_finding():
    """A single-digit misread of a component is localised: the finding names the
    suspect and the casting-implied value (real case: debtors 7,888,837 vs 831)."""
    bs = Statement("balance_sheet", [
        line("stocks", "Stocks", 349054, 349054),
        line("debtors", "Debtors", 7888837, 7888837),   # misread: true is 7888831
        line("cash", "Cash", 2130087, 2130087),
        line("total_ca", "Current assets", 10367972, 10367972,
             deriv=(("stocks", 1), ("debtors", 1), ("cash", 1))),
    ])
    fs = FinancialStatements("T", "2025-12-31", rounding_unit=D(1),
                             statements={"balance_sheet": bs})
    findings = [f for f in check_casting(fs) if f.check_type == "cast"]
    assert findings
    assert "PROBABLE OCR MISREAD" in findings[0].description
    assert "7,888,831" in findings[0].description  # the casting-implied correction


def test_real_cast_error_not_misflagged_as_ocr():
    """A large, non-digit-close discrepancy is a genuine finding, not 'OCR'."""
    bs = Statement("balance_sheet", [
        line("a", "A", 100, 100),
        line("b", "B", 200, 200),
        line("total", "Total", 900, 900, deriv=(("a", 1), ("b", 1))),  # 300 vs 900
    ])
    fs = FinancialStatements("T", "2025-12-31", rounding_unit=D(1),
                             statements={"balance_sheet": bs})
    f = next(x for x in check_casting(fs) if x.check_type == "cast")
    assert "PROBABLE OCR MISREAD" not in f.description


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
