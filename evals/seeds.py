"""Seeded-defect generators for the numerical + formatting gate eval.

Each seed mutates the clean reference accounts to introduce ONE known defect and
returns the findings the gate produced plus a predicate that recognises the
expected catch. Recall = fraction of seeds whose defect the gate catches; the
clean model's own false-positive rate is measured separately (must be 0).
"""

from __future__ import annotations

import copy
from collections.abc import Callable

from pipeline.validate.checks import Finding, validate
from pipeline.validate.formatting import check_formatting
from pipeline.validate.fs_model import from_dict

PRESENT_NOTES = ["5", "6"]
Seed = Callable[[dict], tuple[str, list[Finding], Callable[[list[Finding]], bool]]]


def _set(model: dict, statement: str, line_id: str, field: str, value) -> dict:
    m = copy.deepcopy(model)
    for it in m["statements"][statement]["items"]:
        if it["id"] == line_id:
            it[field] = value
    return m


def seed_break_cast(clean: dict):
    m = _set(clean, "income", "gross_profit", "current", 999999)
    findings = validate(from_dict(m))
    return ("break_cast", findings,
            lambda fs: any(f.check_type == "cast" and "gross_profit" in f.location
                           for f in fs))


def seed_break_balance(clean: dict):
    m = _set(clean, "balance_sheet", "total_equity", "current", 310000)
    findings = validate(from_dict(m))
    return ("break_balance", findings,
            lambda fs: any("balance" in f.description.lower() for f in fs))


def seed_digit_misread(clean: dict):
    m = _set(clean, "balance_sheet", "debtors", "current", 150006)   # +6, OCR-like
    findings = validate(from_dict(m))
    return ("digit_misread", findings,
            lambda fs: any("OCR MISREAD" in f.description for f in fs))


def seed_break_ratio(clean: dict):
    m = _set(clean, "income", "tax_at_rate", "current", 40000)
    findings = validate(from_dict(m))
    return ("break_ratio", findings,
            lambda fs: any(f.check_type == "ratio" for f in fs))


def seed_break_note_crosscast(clean: dict):
    m = copy.deepcopy(clean)
    for it in m["notes"]["5"]["items"]:               # note casts internally, but
        if it["id"] == "c0":
            it["current"] = 110000                    # disagrees with the face figure
        if it["id"] == "total":
            it["current"] = 160000
    findings = validate(from_dict(m))
    return ("break_note_crosscast", findings,
            lambda fs: any(f.check_type == "cross_reference"
                           and "Debtors note" in f.description for f in fs))


def seed_note_gap(clean: dict):
    findings = check_formatting(from_dict(clean), ["5", "8"])   # gap 6,7
    return ("note_gap", findings,
            lambda fs: any(f.check_type == "note_numbering" for f in fs))


def seed_broken_xref(clean: dict):
    findings = check_formatting(from_dict(clean), ["5"])        # note 6 referenced, absent
    return ("broken_xref", findings,
            lambda fs: any(f.check_type == "cross_reference_note" and "6" in f.location
                           for f in fs))


ALL_SEEDS: list[Seed] = [
    seed_break_cast, seed_break_balance, seed_digit_misread, seed_break_ratio,
    seed_break_note_crosscast, seed_note_gap, seed_broken_xref,
]
