"""Front-half review: the directors' report and strategic report against the
Companies Act 2006 and SI 2008/410 Sch 7 (CLAUDE.md locked scope).

The front half is reviewed under company law, not FRS 102. This checks a starter
set of the standard statutory directors'-report disclosures against the
front-half narrative (the pages before the primary statements), reusing the
presence machinery. The requirement set is a STARTER for human review/extension
(it asserts company-law content); conditional items (e.g. the >250-employee
disclosures) are flagged in their text rather than auto-scoped.
"""

from __future__ import annotations

from pipeline.engine.checklist import EngineResult, Requirement
from pipeline.engine.presence import PresenceResult, check_presence
from pipeline.extract.structure import classify_table
from pipeline.llm_client import LLMClient

# (citation, ref, requirement text). Severity 'statutory' — company-law items.
FRONT_HALF_REQUIREMENTS: list[tuple[str, str, str]] = [
    ("CA06", "s416(1)(a)",
     "The directors' report must state the names of the persons who were "
     "directors during the financial year."),
    ("CA06", "s416(3)",
     "The directors' report must state the amount (if any) the directors "
     "recommend should be paid by way of dividend."),
    ("SI2008/410", "Sch7 para7",
     "The directors' report must give an indication of likely future "
     "developments in the business of the company."),
    ("SI2008/410", "Sch7 para6",
     "The directors' report must disclose the company's financial risk "
     "management objectives and policies and its exposure to price, credit, "
     "liquidity and cash flow risk, unless not material."),
    ("CA06", "s418",
     "The directors' report must contain a statement that, so far as each "
     "director is aware, there is no relevant audit information of which the "
     "auditor is unaware, and that each director has taken the steps they ought "
     "to have taken to make themselves aware of it."),
    ("FRC", "directors_responsibilities",
     "The accounts should include a statement of directors' responsibilities "
     "in respect of the financial statements."),
    ("FRS102/CA06", "going_concern_fronthalf",
     "The directors' report or strategic report should address the going "
     "concern basis of preparation."),
    ("SI2008/410", "Sch7 para11",
     "If the company had on average more than 250 employees, the directors' "
     "report must contain a statement on employee engagement (how directors "
     "have engaged with employees). [Conditional on >250 employees.]"),
    ("SI2008/410", "Sch7 para10",
     "If the company had on average more than 250 employees, the directors' "
     "report must describe its policy on the employment of disabled persons. "
     "[Conditional on >250 employees.]"),
]


def _is_highlights_table(table: dict) -> bool:
    """A Strategic-Report financial-highlights / year-on-year movement table —
    NOT a primary statement. These carry a 'Change' and/or '%' column, which a
    profit-and-loss account or balance sheet never does. They appear in the front
    half and must not be mistaken for the start of the primary statements
    (otherwise the directors'/strategic report below them is cut from review)."""
    cells = {(c.get("content") or "").strip().lower() for c in table.get("cells", [])}
    return "change" in cells or "%" in cells


def first_statement_page(layout: dict) -> int:
    """Page on which the primary statements begin (the front-half cutoff).

    A genuine primary statement is an income/balance-sheet table that is NOT a
    highlights/movement table. Without this guard, a financial-highlights table in
    the Strategic Report is read as the profit-and-loss account and the whole
    directors'/strategic report below it is excluded from the front-half review.
    """
    pages = [t["boundingRegions"][0]["pageNumber"]
             for t in layout.get("tables", []) or []
             if classify_table(t) in ("income", "balance_sheet")
             and not _is_highlights_table(t)
             and t.get("boundingRegions")]
    return min(pages) if pages else 9999


def gather_front_half(layout: dict) -> str:
    cutoff = first_statement_page(layout)
    return "\n".join(
        (p.get("content") or "").strip()
        for p in layout.get("paragraphs", []) or []
        if p.get("content")
        and (p.get("boundingRegions") or [{}])[0].get("pageNumber", 0) < cutoff)


def _requirements() -> list[EngineResult]:
    out = []
    for source, ref, text in FRONT_HALF_REQUIREMENTS:
        req = Requirement(f"fh-{ref}", source, ref, "both", text, "always", None,
                          (), "missing", "statutory")
        out.append(EngineResult(req, "applicable"))
    return out


def review_front_half(layout: dict, client: LLMClient) -> list[PresenceResult]:
    """Presence-check the statutory front-half disclosures; absent => finding."""
    narrative = gather_front_half(layout)
    if not narrative.strip():
        return []
    return check_presence(_requirements(), narrative, client)
