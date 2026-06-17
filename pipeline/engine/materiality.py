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


def _income_line(fs: FinancialStatements, *keywords: str) -> Decimal | None:
    stmt = fs.statements.get("income")
    if stmt is None:
        return None
    for it in stmt.items:
        label = (it.label or "").lower()
        if any(k in label for k in keywords) and it.current is not None:
            return it.current
    return None


def extract_benchmarks(fs: FinancialStatements) -> dict[str, Decimal | None]:
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
    return {"pbt": pbt, "turnover": turnover, "gross_assets": gross_assets}


def compute_materiality(benchmarks: dict[str, Decimal | None]) -> Materiality:
    pbt = benchmarks.get("pbt")
    turnover = benchmarks.get("turnover")
    gross = benchmarks.get("gross_assets")
    if pbt is not None and pbt > 0:
        return Materiality("5% of profit before tax", (pbt * PBT_RATE).quantize(Decimal(1)))
    # loss-making (or nil/None PBT): 1% of turnover (owner rule)
    if turnover is not None and turnover != 0:
        return Materiality("1% of turnover (loss-making)",
                           (abs(turnover) * TURNOVER_RATE).quantize(Decimal(1)))
    if gross is not None and gross != 0:
        return Materiality("1% of gross assets (no turnover)",
                           (abs(gross) * GROSS_ASSETS_RATE).quantize(Decimal(1)))
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
