"""Deterministic numerical validation gate (CLAUDE.md hard rule 1: never an LLM).

Operates only on the typed FinancialStatements model. Two primitives express
the whole CLAUDE.md numerical suite:

- derivation checks: every derived LineItem (signed sum of sibling lines) must
  equal its stated value, within rounding tolerance. Covers casting of every
  statement and note, subtotals, net assets, reserves articulation
  (opening +/- movements = closing) and cash-flow movement.
- equality checks: declared cross-references must match. Covers balance-sheet
  balancing (net assets = total equity), note->face cross-cast, cash-flow
  reconciliation (net movement = change in BS cash), and front-half ties.

Plus a comparatives presence check. Missing values are never coerced to 0
(hard rule 5): a check that cannot evaluate emits an explicit error finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pipeline.validate.fs_model import FinancialStatements, LineItem

COLUMNS = ("current", "prior")


@dataclass(frozen=True)
class Finding:
    check_type: str          # 'cast' | 'cross_reference' | 'comparative' | 'eval_error'
    location: str            # where in the accounts
    description: str
    severity: str            # 'statutory' | 'standard-material' | 'standard-immaterial-candidate'
    is_error: bool = False   # True => check could not be evaluated (extraction gap)
    expected: str | None = None
    actual: str | None = None


def _tolerance(fs: FinancialStatements, n_components: int) -> Decimal:
    """Rounding allowance: a signed sum of n figures each rounded to the unit can
    drift up to ~n/2 units from a separately-rounded stated total. Allow that,
    with a floor of one unit."""
    return fs.rounding_unit * max(1, (n_components + 1) // 2)


def _eval_derivation(line: LineItem, index: dict[str, LineItem],
                     column: str) -> tuple[Decimal | None, str | None]:
    total = Decimal(0)
    for comp_id, sign in line.derivation or ():
        comp = index.get(comp_id)
        if comp is None:
            return None, f"component {comp_id!r} not found"
        value = getattr(comp, column)
        if value is None:
            return None, f"component {comp_id!r} has no {column} value"
        total += sign * value
    return total, None


def _digit_close(a: Decimal, b: Decimal) -> bool:
    """Do two figures look like an OCR digit-misread of each other — same number
    of digits, differing in at most two positions, AND the magnitude change is
    small relative to the figure (so 7,888,837 vs 7,888,831 qualifies, but
    100 vs 700 — a 600% jump — does not)?"""
    if a == b:
        return False
    sa, sb = str(abs(int(a))), str(abs(int(b)))
    if len(sa) != len(sb):
        return False
    if sum(x != y for x, y in zip(sa, sb, strict=True)) > 2:
        return False
    return abs(a - b) * 100 < abs(a)   # < 1% relative change


def _ocr_hint(line: LineItem, index: dict[str, LineItem], column: str,
              stated: Decimal, computed: Decimal) -> str:
    """If a single component (or the total) being a digit-misread would resolve
    the cast, point at the likely culprit and the casting-implied value. The
    statements over-determine the figures, so this localises OCR errors."""
    delta = computed - stated
    # (confidence, text) per suspect; lower OCR confidence = more likely culprit
    suspects: list[tuple[float, str]] = []
    for comp_id, sign in line.derivation or ():
        comp = index.get(comp_id)
        v = None if comp is None else getattr(comp, column)
        if v is None:
            continue
        implied = v - sign * delta           # value this component needs for the cast
        if _digit_close(v, implied):
            cf = comp.confidence_for(column)
            conf = cf if cf is not None else 1.0
            ctxt = f" [OCR confidence {cf:.3f}]" if cf is not None else ""
            suspects.append((conf, f"{comp.label!r} read {v:,} but casting implies "
                                   f"{implied:,}{ctxt}"))
    if _digit_close(stated, computed):
        suspects.append((1.0, f"the total {line.label!r} read {stated:,} but "
                              f"components imply {computed:,}"))
    if not suspects:
        return ""
    suspects.sort(key=lambda s: s[0])        # lowest-confidence first
    lead = " (most likely the first)" if suspects[0][0] < 0.99 else ""
    return (" PROBABLE OCR MISREAD (single digit), candidates by ascending OCR "
            f"confidence{lead}: " + "; ".join(t for _, t in suspects)
            + " — re-read/verify before treating as a finding.")


def _check_container(name: str, items: list[LineItem], index: dict[str, LineItem],
                     fs: FinancialStatements) -> list[Finding]:
    findings: list[Finding] = []
    for line in items:
        if line.derivation is None:
            continue
        tol = _tolerance(fs, len(line.derivation))
        for column in COLUMNS:
            if column == "prior" and not fs.has_comparatives:
                continue
            stated = getattr(line, column)
            computed, err = _eval_derivation(line, index, column)
            if err is not None:
                if stated is not None:
                    findings.append(Finding(
                        "eval_error", f"{name}:{line.id}",
                        f"Cannot verify cast of '{line.label}' ({column}): {err}",
                        "standard-material", is_error=True))
                continue
            if stated is None:
                findings.append(Finding(
                    "eval_error", f"{name}:{line.id}",
                    f"Derived line '{line.label}' has no stated {column} value to "
                    "check against",
                    "standard-material", is_error=True))
                continue
            if abs(stated - computed) > tol:
                hint = _ocr_hint(line, index, column, stated, computed)
                findings.append(Finding(
                    "cast", f"{name}:{line.id}",
                    f"'{line.label}' ({column}) does not cast: components sum to "
                    f"{computed}, statement shows {stated} (tolerance {tol})." + hint,
                    "standard-material",
                    expected=str(computed), actual=str(stated)))
    return findings


def check_casting(fs: FinancialStatements) -> list[Finding]:
    findings: list[Finding] = []
    for stmt in fs.statements.values():
        findings += _check_container(stmt.name, stmt.items, stmt.by_id(), fs)
    for note in fs.notes.values():
        findings += _check_container(f"note {note.number}", note.items,
                                     note.by_id(), fs)
    return findings


def check_equalities(fs: FinancialStatements) -> list[Finding]:
    findings: list[Finding] = []
    for eq in fs.equalities:
        left, right = fs.resolve(eq.left), fs.resolve(eq.right)
        if left is None or right is None:
            missing = eq.left if left is None else eq.right
            findings.append(Finding(
                "eval_error", eq.description,
                f"{eq.description}: reference {missing!r} does not resolve",
                "standard-material", is_error=True))
            continue
        tol = _tolerance(fs, 2)
        for column in COLUMNS:
            if column == "prior" and not fs.has_comparatives:
                continue
            lv, rv = getattr(left, column), getattr(right, column)
            if lv is None and rv is None:
                continue
            if lv is None or rv is None:
                findings.append(Finding(
                    "eval_error", eq.description,
                    f"{eq.description} ({column}): one side has no value "
                    f"({left.label}={lv}, {right.label}={rv})",
                    "standard-material", is_error=True))
                continue
            if abs(lv - rv) > tol:
                findings.append(Finding(
                    "cross_reference", eq.description,
                    f"{eq.description} ({column}): {left.label}={lv} != "
                    f"{right.label}={rv} (tolerance {tol})",
                    "standard-material", expected=str(lv), actual=str(rv)))
    return findings


def check_ratios(fs: FinancialStatements) -> list[Finding]:
    findings: list[Finding] = []
    for rc in fs.ratio_checks:
        target, base = fs.resolve(rc.target), fs.resolve(rc.base)
        if target is None or base is None:
            missing = rc.target if target is None else rc.base
            findings.append(Finding(
                "eval_error", rc.description,
                f"{rc.description}: reference {missing!r} does not resolve",
                "standard-material", is_error=True))
            continue
        for column in COLUMNS:
            if column == "prior" and not fs.has_comparatives:
                continue
            tv, bv = getattr(target, column), getattr(base, column)
            if tv is None and bv is None:
                continue
            if tv is None or bv is None:
                findings.append(Finding(
                    "eval_error", rc.description,
                    f"{rc.description} ({column}): missing value "
                    f"({target.label}={tv}, {base.label}={bv})",
                    "standard-material", is_error=True))
                continue
            expected = bv * rc.rate
            # product rounding: allow rounding of base and of the stated target
            tol = fs.rounding_unit * 2
            if abs(tv - expected) > tol:
                findings.append(Finding(
                    "ratio", rc.description,
                    f"{rc.description} ({column}): {target.label}={tv} != "
                    f"{base.label} x {rc.rate} = {expected} (tolerance {tol})",
                    "standard-material", expected=str(expected), actual=str(tv)))
    return findings


def check_comparatives(fs: FinancialStatements) -> list[Finding]:
    """Detect a WHOLESALE-missing comparative column (a CA06/Sch 1 breach), not
    individual new line items — a provision first recognised this year, or a nil
    prior, legitimately has no comparative and must not be flagged. Heuristic: if
    almost every value-bearing line lacks a prior, the comparative column is
    absent."""
    if not fs.has_comparatives:
        return []
    containers: list[tuple[str, list[LineItem]]] = [
        (s.name, s.items) for s in fs.statements.values()]
    containers += [(f"note {n.number}", n.items) for n in fs.notes.values()]
    findings: list[Finding] = []
    for name, items in containers:
        valued = [ln for ln in items if ln.current is not None]
        if len(valued) < 4:
            continue
        missing = [ln for ln in valued if ln.prior is None]
        if len(missing) / len(valued) >= 0.8:
            findings.append(Finding(
                "comparative", name,
                f"comparative (prior-year) column appears absent in {name}: "
                f"{len(missing)} of {len(valued)} value lines have no comparative",
                "standard-material", is_error=False))
    return findings


LOW_CONFIDENCE = 0.95


def check_low_confidence(fs: FinancialStatements,
                         threshold: float = LOW_CONFIDENCE) -> list[Finding]:
    """Flag extracted figures whose OCR confidence is below threshold — the
    backstop for a misread that does not happen to break any cast/cross-cast."""
    findings: list[Finding] = []
    for stmt in fs.statements.values():
        for ln in stmt.items:
            for column in COLUMNS:
                cf = ln.confidence_for(column)
                value = getattr(ln, column)
                if cf is not None and cf < threshold and value is not None:
                    findings.append(Finding(
                        "low_confidence", f"{stmt.name}:{ln.id}",
                        f"'{ln.label}' {column} figure {value:,} extracted at low OCR "
                        f"confidence {cf:.3f} — verify against the document",
                        "standard-material", is_error=True))
    return findings


def validate(fs: FinancialStatements) -> list[Finding]:
    """Run the full deterministic numerical gate; returns all findings."""
    return (check_casting(fs) + check_equalities(fs) + check_ratios(fs)
            + check_comparatives(fs) + check_low_confidence(fs))
