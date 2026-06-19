"""Materiality computation and severity grading.

Benchmark (owner rule): a profit-making entity uses 5% of profit before tax; a
loss-making entity uses 1% of turnover; failing that (no turnover), 1% of gross
assets. The basis and value are logged on the engagement and may be overridden.

Materiality GRADES severity but never waives statutory items (CLAUDE.md): a
non-statutory numerical finding whose magnitude is below materiality is
re-graded to 'standard-immaterial-candidate'.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

from pipeline.validate.checks import Finding
from pipeline.validate.fs_model import FinancialStatements

PBT_RATE = Decimal("0.05")
TURNOVER_RATE = Decimal("0.01")
GROSS_ASSETS_RATE = Decimal("0.01")


@dataclass(frozen=True)
class Materiality:
    basis: str
    value: Decimal | None
    overridden: bool = False


def _income_line(fs: FinancialStatements, *keywords: str,
                 column: str = "current") -> Decimal | None:
    stmt = fs.statements.get("income")
    if stmt is None:
        return None
    for it in stmt.items:
        label = (it.label or "").lower()
        value = it.prior if column == "prior" else it.current
        if any(k in label for k in keywords) and value is not None:
            return value
    return None


def extract_benchmarks(fs: FinancialStatements) -> dict[str, Decimal | None]:
    """Current- AND prior-year benchmarks. The accounts present two years on the
    face, so disclosure/materiality decisions must consider both (Phil's rule):
    e.g. an accounting policy whose balance is immaterial this year may be
    material in the prior year and the policy still has to be disclosed."""
    pbt = _income_line(fs, "before tax", "before taxation")
    turnover = _income_line(fs, "turnover", "revenue")
    gross_assets = None
    bs = fs.statements.get("balance_sheet")
    if bs is not None:
        fa = next((it.current for it in bs.items
                   if "total_fixed" in it.id and it.current is not None), None)
        ca = next((it.current for it in bs.items
                   if "total_current" in it.id and it.current is not None), None)
        if fa is not None and ca is not None:
            gross_assets = fa + ca
    return {
        "pbt": pbt, "turnover": turnover, "gross_assets": gross_assets,
        "pbt_prior": _income_line(fs, "before tax", "before taxation",
                                  column="prior"),
        "turnover_prior": _income_line(fs, "turnover", "revenue", column="prior"),
    }


def _graded(value: Decimal) -> Decimal | None:
    """Quantize to the unit; None if it rounds below 1 (a benchmark that yields a
    materiality of 0 is unusable — almost always an extraction miss, e.g. turnover
    read as 0 — so fall through to the next basis rather than returning 0)."""
    v = value.quantize(Decimal(1))
    return v if v >= 1 else None


def compute_materiality(benchmarks: dict[str, Decimal | None]) -> Materiality:
    pbt = benchmarks.get("pbt")
    turnover = benchmarks.get("turnover")
    gross = benchmarks.get("gross_assets")
    if pbt is not None and pbt > 0 and (v := _graded(pbt * PBT_RATE)) is not None:
        return Materiality("5% of profit before tax", v)
    # loss-making (or nil/None PBT): 1% of turnover (owner rule)
    if (turnover is not None and turnover != 0
            and (v := _graded(abs(turnover) * TURNOVER_RATE)) is not None):
        return Materiality("1% of turnover (loss-making)", v)
    if (gross is not None and gross != 0
            and (v := _graded(abs(gross) * GROSS_ASSETS_RATE)) is not None):
        return Materiality("1% of gross assets (no turnover)", v)
    return Materiality("undetermined — set manually", None)


def grade_findings(findings: list[Finding], materiality: Materiality) -> list[Finding]:
    """Re-grade non-statutory numerical findings below materiality to immaterial
    candidates; statutory items and unquantifiable findings are untouched."""
    if materiality.value is None:
        return findings
    out: list[Finding] = []
    for f in findings:
        if (f.severity != "statutory" and not f.is_error
                and f.expected is not None and f.actual is not None):
            try:
                magnitude = abs(Decimal(f.expected) - Decimal(f.actual))
            except InvalidOperation:
                magnitude = None
            if magnitude is not None and magnitude < materiality.value:
                f = replace(f, severity="standard-immaterial-candidate")
        out.append(f)
    return out
