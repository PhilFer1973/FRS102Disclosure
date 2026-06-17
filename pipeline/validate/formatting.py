"""Mechanical formatting / consistency checks (pure code, deterministic).

The fourth finding pillar (CLAUDE.md): formatting and consistency defects. These
need no checklist rules and no LLM — they catch what the maths and disclosure
passes do not: a note-numbering gap, or a face cross-reference pointing at a note
that is not in the accounts. More mechanical checks (unit consistency, rounding
uniformity, date logic) attach here as their inputs become available from
extraction.
"""

from __future__ import annotations

import re
from collections import Counter

from pipeline.validate.checks import Finding
from pipeline.validate.fs_model import FinancialStatements


def check_note_numbering(present: list[str]) -> list[Finding]:
    """Gaps and duplicates in the note-number sequence. Letter-suffixed notes
    (1A) are ignored for the gap test; pure integers drive it."""
    findings: list[Finding] = []
    for num, count in Counter(present).items():
        if count > 1:
            findings.append(Finding(
                "note_numbering", f"note {num}",
                f"Note number {num} appears more than once in the accounts",
                "standard-material"))
    ints = sorted({int(n) for n in present if re.fullmatch(r"\d+", n)})
    if ints:
        missing = [n for n in range(ints[0], ints[-1] + 1) if n not in ints]
        for n in missing:
            findings.append(Finding(
                "note_numbering", f"note {n}",
                f"Note numbering gap: note {n} is absent between notes "
                f"{ints[0]} and {ints[-1]} — confirm the sequence is intentional",
                "standard-immaterial-candidate"))
    return findings


def check_cross_references(referenced: set[str], present: set[str]) -> list[Finding]:
    """Every note a statement line points to must exist in the accounts."""
    findings: list[Finding] = []
    for ref in sorted(referenced - present, key=lambda s: (len(s), s)):
        findings.append(Finding(
            "cross_reference_note", f"note {ref}",
            f"A primary-statement line references note {ref}, which is not "
            "present in the accounts (broken cross-reference)",
            "standard-material"))
    return findings


def check_formatting(fs: FinancialStatements, present_notes: list[str]) -> list[Finding]:
    referenced = {it.note_ref for st in fs.statements.values()
                  for it in st.items if it.note_ref}
    return (check_note_numbering(present_notes)
            + check_cross_references(referenced, set(present_notes)))
