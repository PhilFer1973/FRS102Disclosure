"""Structured review summary — the JSON contract between the Python pipeline and
the MCP app front end.

The MCP `review_accounts` tool returns this object; the at-a-glance panel reads
`entity`, `materiality.display` and `counts`, and the detailed findings list
renders in the chat beneath it. Category mapping mirrors the Excel register
(pipeline/assemble/register.py) so the two never disagree.
"""

from __future__ import annotations

from decimal import Decimal

from pipeline.engine.materiality import Materiality
from pipeline.validate.checks import Finding

_FORMATTING = {"note_numbering", "cross_reference_note"}


def humanize_money(value: Decimal | float | None) -> str:
    """193481 -> '£193k'; 26350000 -> '£26.4m'; None -> 'n/a'."""
    if value is None:
        return "n/a"
    v = abs(int(value))
    if v >= 1_000_000:
        return f"£{v / 1_000_000:.1f}m"
    if v >= 1_000:
        return f"£{round(v / 1_000)}k"
    return f"£{v:,}"


def _category(check_type: str) -> str:
    if check_type in _FORMATTING:
        return "formatting"
    if check_type == "judgment":
        return "judgement"
    return "numerical"


def build_summary(entity: str, period_end: str, materiality: Materiality,
                  numerical: list[Finding], presence: list, questions: list) -> dict:
    """Assemble the at-a-glance summary + detailed findings the MCP app consumes."""
    by_cat = {"judgement": 0, "disclosure": 0, "numerical": 0, "formatting": 0}
    findings: list[dict] = []
    seen: set[tuple[str, str, str]] = set()   # collapse duplicate active rules

    def add(row: dict) -> None:
        key = (row["category"], row["citation"], row["text"])
        if key in seen:
            return
        seen.add(key)
        by_cat[row["category"]] += 1
        findings.append(row)

    for f in numerical:
        cat = _category(f.check_type)
        add({"category": cat, "citation": f.location,
             "severity": f.severity, "text": f.description})
    for p in presence:
        if p.status == "present":
            continue
        req = p.requirement.requirement
        lead = "Missing: " if p.status == "absent" else "Verify: "
        add({"category": "disclosure", "citation": f"{req.source} {req.reference}",
             "severity": req.severity, "status": p.status,
             "text": lead + req.requirement_text})
    return {
        "entity": entity,
        "period_end": period_end,
        "materiality": {
            "value": float(materiality.value) if materiality.value is not None else None,
            "basis": materiality.basis,
            "display": humanize_money(materiality.value),
        },
        "counts": {
            "total_findings": sum(by_cat.values()),
            "by_category": by_cat,
            "need_judgement": by_cat["judgement"],
            "questions": len(questions),
        },
        "findings": findings,
        "questions": [{"fact_key": q.fact_key, "question": q.question_text,
                       "citation": ", ".join(q.affected_refs)} for q in questions],
    }
