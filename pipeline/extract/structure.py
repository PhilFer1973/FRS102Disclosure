"""LLM-assisted structuring: extracted statement rows -> typed FS model.

The model proposes STRUCTURE ONLY — for each line, a stable id and (for
subtotals/totals) the signed component ids it casts from, plus which lines are
net assets and total equity. It never supplies or alters figures: every value
is bound from the deterministic extraction (tables.ExtractedRow) by row index.
The deterministic numerical gate then verifies the arithmetic, so a wrong
structure surfaces as a cast/cross-reference finding rather than a silent error.
"""

from __future__ import annotations

import re
from decimal import Decimal

from pipeline.extract.tables import (
    ExtractedRow,
    WordSpans,
    extract_statement,
    word_spans,
)
from pipeline.llm_client import LLMClient
from pipeline.validate.fs_model import (
    Equality,
    FinancialStatements,
    LineItem,
    Note,
    Statement,
)

# Note heading: 'N. Title'. The title may contain parentheses (6. Operating
# (loss)/profit) and be long (3. Judgments in applying accounting policies and
# key sources of estimation uncertainty), but contains no sentence period — the
# discriminator from prose that merely begins 'N.'. '(continued)' excluded.
_NOTE_HEADING = re.compile(r"^(\d{1,2})\.\s+([^.]+?)\s*$")
_NOTE_HEADING_MAXLEN = 120
# Lenient note-NUMBER detector for the formatting checks: a note number is
# present if a paragraph begins 'N. ' (a space after the period — so sub-numbered
# policy items like '2.1' don't match). Robust to title quirks (parentheses, long
# titles, OCR double-periods) that defeat title parsing.
_NOTE_NUMBER = re.compile(r"^(\d{1,2})\.\s")


def note_numbers_present(layout: dict) -> list[str]:
    seen: set[str] = set()
    for p in layout.get("paragraphs", []) or []:
        content = (p.get("content") or "").strip()
        if "(continued)" in content:
            continue
        m = _NOTE_NUMBER.match(content)
        if m:
            seen.add(m.group(1))
    return sorted(seen, key=int)

STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "id": {"type": "string"},
                    "derivation": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "component_id": {"type": "string"},
                                "sign": {"type": "integer", "enum": [1, -1]},
                            },
                            "required": ["component_id", "sign"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["index", "id", "derivation"],
                "additionalProperties": False,
            },
        },
        "net_assets_id": {"type": ["string", "null"]},
        "total_equity_id": {"type": ["string", "null"]},
    },
    "required": ["lines", "net_assets_id", "total_equity_id"],
    "additionalProperties": False,
}

STRUCTURE_SYSTEM = """\
You receive the line items of one primary statement from a UK FRS 102 set of
accounts (a profit & loss account or a balance sheet), each with its index,
label and figures. Identify STRUCTURE only — you must not change, supply or
restate any figure.

For each line:
- Assign a short snake_case `id` (e.g. turnover, gross_profit, net_assets).
- If the line is a SUBTOTAL or TOTAL — its value is the signed sum of other
  lines — give `derivation`: the list of component lines with sign +1 (added)
  or -1 (subtracted). A leaf line (a directly-stated figure) has derivation null.
- Use the figures shown ONLY to check which components sum to each subtotal;
  the figures themselves are authoritative and supplied separately.

Unlabelled rows are usually subtotals (e.g. a blank row whose value equals the
sum of the lines just above it). For a balance sheet, also set:
- net_assets_id: the 'Net assets' (or 'Net assets'/'Total net assets') line.
- total_equity_id: the total of capital and reserves / shareholders' funds
  (often an unlabelled total at the foot of the capital-and-reserves section).
For a profit & loss account set both to null.

Ignore memo/alternative-performance lines (e.g. EBITDA) — give them null
derivation and a descriptive id; do not use them as components of statutory
subtotals.
"""


def _rows_for_prompt(rows: list[ExtractedRow]) -> str:
    out = []
    for i, r in enumerate(rows):
        cur = "" if r.current is None else f"{r.current:,}"
        pri = "" if r.prior is None else f"{r.prior:,}"
        out.append(f"{i}: {r.label!r} | current={cur} | prior={pri}")
    return "\n".join(out)


def structure_statement(name: str, rows: list[ExtractedRow],
                        client: LLMClient) -> dict:
    user = (f"Statement: {name}\n\nLines (index: label | figures):\n"
            + _rows_for_prompt(rows))
    return client.complete_json("structure", STRUCTURE_SYSTEM, user,
                                STRUCTURE_SCHEMA, max_tokens=3000)


def build_statement(name: str, rows: list[ExtractedRow], structure: dict) -> Statement:
    """Bind LLM structure to deterministically-extracted values (values from
    `rows` only). Returns a Statement plus discovered net_assets/total_equity ids
    via attributes on the returned object are not used; see assemble()."""
    by_index = {ln["index"]: ln for ln in structure["lines"]}
    ids_used: set[str] = set()
    items: list[LineItem] = []
    for i, r in enumerate(rows):
        ln = by_index.get(i)
        if ln is None:
            continue  # LLM dropped this row (e.g. section header with no figure)
        lid = ln["id"]
        if lid in ids_used:
            lid = f"{lid}_{i}"  # ensure uniqueness
        ids_used.add(lid)
        deriv = None
        if ln.get("derivation"):
            deriv = tuple((c["component_id"], c["sign"]) for c in ln["derivation"])
        items.append(LineItem(id=lid, label=r.label or f"(line {i})",
                              current=r.current, prior=r.prior, derivation=deriv,
                              note_ref=r.note,
                              current_confidence=r.current_confidence,
                              prior_confidence=r.prior_confidence))
    return Statement(name=name, items=items)


def classify_table(table: dict) -> str | None:
    """Keyword classifier: which primary statement (if any) this table is."""
    # Normalise whitespace so a line-wrapped subtotal ('Total assets less\ncurrent
    # liabilities') still matches as a single phrase.
    labels = " ".join(
        " ".join((c.get("content") or "").lower() for c in table["cells"]).split())
    # Balance sheet: an asset/liability structure. Match the classic subtotals OR
    # 'fixed assets' alongside a balance-sheet-only line (net current assets /
    # shareholders' funds — older UK style). Requiring 'fixed assets' for that
    # second path keeps the statement of changes in equity (share capital /
    # premium / total equity, no fixed assets) from being read as a balance sheet.
    if ("net assets" in labels or "total assets less current" in labels):
        return "balance_sheet"
    if "fixed assets" in labels and ("shareholders' funds" in labels
                                     or "net current assets" in labels
                                     or "called up share capital" in labels):
        return "balance_sheet"
    if "turnover" in labels and ("gross profit" in labels
                                 or "operating" in labels):
        return "income"
    return None


def _poly_top(obj: dict) -> float:
    br = (obj.get("boundingRegions") or [{}])[0]
    poly = br.get("polygon") or []
    ys = poly[1::2]
    return min(ys) if ys else 1e9


def _note_headings(layout: dict) -> list[dict]:
    """Note-number headings ('14. Debtors') with page + vertical position, for
    associating each note table with its note number."""
    out, seen = [], set()
    for p in layout.get("paragraphs", []) or []:
        content = (p.get("content") or "").strip()
        if len(content) > _NOTE_HEADING_MAXLEN or "(continued)" in content:
            continue
        m = _NOTE_HEADING.match(content)
        if not m:
            continue
        num = m.group(1)
        if num in seen:                       # keep the first occurrence only
            continue
        seen.add(num)
        page = (p.get("boundingRegions") or [{}])[0].get("pageNumber")
        out.append({"number": num, "title": m.group(2).strip(),
                    "page": page, "top": _poly_top(p)})
    return out


def _note_number_for(table: dict, headings: list[dict]) -> str | None:
    page = (table.get("boundingRegions") or [{}])[0].get("pageNumber")
    top = _poly_top(table)
    on_page = [h for h in headings if h["page"] == page and h["top"] <= top + 0.1]
    return max(on_page, key=lambda h: h["top"])["number"] if on_page else None


def _add_note_crosscasts(fs: FinancialStatements, layout: dict, ws: WordSpans,
                         primary_ids: set[int]) -> None:
    """Build referenced note tables and cross-cast each note's total to the face
    line that cites it — an independent second read of the figure. Catches a
    face/note disagreement (e.g. debtors face 7,888,837 vs note 7,888,831)."""
    referenced = {it.note_ref for st in fs.statements.values()
                  for it in st.items if it.note_ref}
    if not referenced:
        return
    headings = _note_headings(layout)
    for table in layout.get("tables", []) or []:
        if id(table) in primary_ids:
            continue
        num = _note_number_for(table, headings)
        if num not in referenced or num in fs.notes:
            continue
        rows = [r for r in extract_statement(table, ws)
                if r.current is not None or r.prior is not None]
        if len(rows) < 2:
            continue
        *components, total_row = rows
        # Only cross-cast SIMPLE ADDITIVE analysis notes (debtors, creditors,
        # stocks): the last row must equal the sum of its components. This
        # excludes movement tables (fixed assets) and reconciliations (tax),
        # whose totals are not a flat sum and need proper structuring (future).
        comp_cur = [c.current for c in components if c.current is not None]
        if (total_row.current is None or len(comp_cur) != len(components)
                or abs(sum(comp_cur) - total_row.current) > Decimal(2)):
            continue
        items = [LineItem(id=f"c{i}", label=c.label or f"(line {i})",
                          current=c.current, prior=c.prior,
                          current_confidence=c.current_confidence,
                          prior_confidence=c.prior_confidence)
                 for i, c in enumerate(components)]
        items.append(LineItem(
            id="total", label=total_row.label or "Total",
            current=total_row.current, prior=total_row.prior,
            derivation=tuple((f"c{i}", 1) for i in range(len(components))),
            current_confidence=total_row.current_confidence,
            prior_confidence=total_row.prior_confidence))
        fs.notes[num] = Note(number=num, title="", items=items)
        for st_name, st in fs.statements.items():
            for it in st.items:
                if it.note_ref == num:
                    fs.equalities.append(Equality(
                        f"note:{num}:total", f"statement:{st_name}:{it.id}",
                        f"note {num} total casts to {it.label} on the {st_name}",
                        compare_abs=True))


def assemble(layout: dict, client: LLMClient,
             entity_name: str = "", period_end: str = "") -> FinancialStatements:
    """Azure Layout result -> structured FinancialStatements (income + balance
    sheet), with per-figure OCR confidence, the balance-sheet balancing equality,
    and note-to-face cross-casts for figures that cite a note."""
    fs = FinancialStatements(entity_name=entity_name, period_end=period_end)
    ws: WordSpans = word_spans(layout)
    primary_ids: set[int] = set()
    for table in layout.get("tables", []) or []:
        kind = classify_table(table)
        if kind not in ("income", "balance_sheet"):
            continue
        primary_ids.add(id(table))
        rows = extract_statement(table, ws)
        structure = structure_statement(kind, rows, client)
        stmt = build_statement(kind, rows, structure)
        fs.statements[kind] = stmt
        if kind == "balance_sheet":
            na, te = structure.get("net_assets_id"), structure.get("total_equity_id")
            ids = {it.id for it in stmt.items}
            if na in ids and te in ids:
                fs.equalities.append(Equality(
                    f"statement:balance_sheet:{na}",
                    f"statement:balance_sheet:{te}",
                    "Balance sheet balances (net assets = total equity)"))
    _add_note_crosscasts(fs, layout, ws, primary_ids)
    return fs
