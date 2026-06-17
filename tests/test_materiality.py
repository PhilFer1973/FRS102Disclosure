from decimal import Decimal

from pipeline.engine.materiality import (
    Materiality,
    compute_materiality,
    extract_benchmarks,
    grade_findings,
)
from pipeline.validate.checks import Finding
from pipeline.validate.fs_model import FinancialStatements, LineItem, Statement

D = Decimal


def _fs(pbt, turnover):
    income = Statement("income", [
        LineItem("turnover", "Turnover", D(turnover)),
        LineItem("pbt", "(Loss)/profit before taxation", D(pbt)),
    ])
    bs = Statement("balance_sheet", [
        LineItem("total_fixed_assets", "", D(1474136), derivation=(("a", 1),)),
        LineItem("total_current_assets", "", D(10847718), derivation=(("b", 1),)),
    ])
    return FinancialStatements("T", "2025-12-31",
                               statements={"income": income, "balance_sheet": bs})


def test_profit_uses_5pct_pbt():
    m = compute_materiality(extract_benchmarks(_fs(1000000, 20000000)))
    assert m.basis.startswith("5% of profit")
    assert m.value == D(50000)


def test_loss_uses_1pct_turnover():
    m = compute_materiality(extract_benchmarks(_fs(-251695, 19348055)))
    assert "turnover" in m.basis
    assert m.value == D(193481)        # 1% of 19,348,055 rounded


def test_no_turnover_falls_back_to_gross_assets():
    b = {"pbt": D(-5000), "turnover": None, "gross_assets": D(2000000)}
    m = compute_materiality(b)
    assert "gross assets" in m.basis and m.value == D(20000)


def test_grade_downgrades_immaterial_non_statutory():
    mat = Materiality("1% of turnover", D(193481))
    findings = [
        Finding("cast", "bs:ca", "off by 6", "standard-material",
                expected="10367978", actual="10367972"),          # tiny -> immaterial
        Finding("cast", "bs:big", "off by 500k", "standard-material",
                expected="5000000", actual="4500000"),            # material -> unchanged
        Finding("cast", "s411", "employee numbers", "statutory",
                expected="100", actual="0"),                      # statutory -> never waived
    ]
    graded = {f.location: f.severity for f in grade_findings(findings, mat)}
    assert graded["bs:ca"] == "standard-immaterial-candidate"
    assert graded["bs:big"] == "standard-material"
    assert graded["s411"] == "statutory"
