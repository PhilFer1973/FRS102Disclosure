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
                findings.append(Finding(
                    "cast", f"{name}:{line.id}",
                    f"'{line.label}' ({column}) does not cast: components sum to "
                    f"{computed}, statement shows {stated} (tolerance {tol})",
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
    if not fs.has_comparatives:
        return []
    findings: list[Finding] = []
    containers: list[tuple[str, list[LineItem]]] = [
        (s.name, s.items) for s in fs.statements.values()]
    containers += [(f"note {n.number}", n.items) for n in fs.notes.values()]
    for name, items in containers:
        for line in items:
            if line.current is not None and line.prior is None:
                findings.append(Finding(
                    "comparative", f"{name}:{line.id}",
                    f"'{line.label}' has a current-year figure but no comparative",
                    "standard-material", is_error=False))
    return findings


def validate(fs: FinancialStatements) -> list[Finding]:
    """Run the full deterministic numerical gate; returns all findings."""
    return (check_casting(fs) + check_equalities(fs) + check_ratios(fs)
            + check_comparatives(fs))
