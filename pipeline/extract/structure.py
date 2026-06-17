"""LLM-assisted structuring: extracted statement rows -> typed FS model.

The model proposes STRUCTURE ONLY — for each line, a stable id and (for
subtotals/totals) the signed component ids it casts from, plus which lines are
net assets and total equity. It never supplies or alters figures: every value
is bound from the deterministic extraction (tables.ExtractedRow) by row index.
The deterministic numerical gate then verifies the arithmetic, so a wrong
structure surfaces as a cast/cross-reference finding rather than a silent error.
"""

from __future__ import annotations

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
    Statement,
)

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
    labels = " ".join((c.get("content") or "").lower() for c in table["cells"])
    if "net assets" in labels or "total assets less current liabilities" in labels:
        return "balance_sheet"
    if "turnover" in labels and ("gross profit" in labels
                                 or "operating" in labels):
        return "income"
    return None


def assemble(layout: dict, client: LLMClient,
             entity_name: str = "", period_end: str = "") -> FinancialStatements:
    """Azure Layout result -> structured FinancialStatements (income + balance
    sheet), with per-figure OCR confidence. Adds the balance-sheet balancing
    equality when both anchor lines are identified."""
    fs = FinancialStatements(entity_name=entity_name, period_end=period_end)
    ws: WordSpans = word_spans(layout)
    for table in layout.get("tables", []) or []:
        kind = classify_table(table)
        if kind not in ("income", "balance_sheet"):
            continue
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
    return fs
