"""Deterministic value extraction from Azure Layout tables.

Turns a Layout table (cells with row/col indices) into clean
(label, note, current, prior) rows for a two-period vertical statement
(profit & loss account, balance sheet). The money parsing and current/prior
assignment are pure code; deciding which lines are subtotals and how they cast
(the derivations) is a separate structuring step — arithmetic itself is always
verified by the deterministic gate, never trusted from an LLM.

Observed convention (UK vertical format): each data row carries exactly two
money figures left-to-right — current year then prior year — even though they
sit in different columns due to the inner/outer subtotal layout. The 'Note'
column is excluded from money parsing so note references aren't read as figures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

NIL = {"-", "—", "–", "nil"}
_MONEY_RE = re.compile(r"^\(?£?\s*-?[\d,]+(?:\.\d+)?\)?$")


def parse_money(s: str | None) -> Decimal | None:
    """'19,348,055' -> 19348055; '(6,567,408)' -> -6567408; '-' -> 0; '' -> None."""
    if s is None:
        return None
    t = s.strip()
    if not t:
        return None
    if t.lower() in NIL:
        return Decimal(0)
    if not _MONEY_RE.match(t):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace("£", "").replace(",", "").replace(" ", "")
    try:
        v = Decimal(t)
    except InvalidOperation:
        return None
    return -v if neg else v


@dataclass(frozen=True)
class ExtractedRow:
    label: str
    note: str | None
    current: Decimal | None
    prior: Decimal | None


def _grid(table: dict) -> tuple[dict[tuple[int, int], str], int, int]:
    g = {}
    for c in table["cells"]:
        g[(c["rowIndex"], c["columnIndex"])] = (c.get("content") or "").replace("\n", " ").strip()
    return g, table["rowCount"], table["columnCount"]


def _note_column(g: dict, cc: int) -> int | None:
    for col in range(cc):
        if g.get((0, col), "").strip().lower() == "note":
            return col
    return None


def extract_statement(table: dict) -> list[ExtractedRow]:
    """Extract (label, note, current, prior) rows from a two-period statement
    table. Header/blank rows yield no usable row and are skipped, but a blank
    label with figures (an unlabelled subtotal) is kept with label ''."""
    g, rc, cc = _grid(table)
    note_col = _note_column(g, cc)
    rows: list[ExtractedRow] = []
    started = False  # skip the leading header band (year / '£' rows)
    for r in range(rc):
        label = g.get((r, 0), "")
        if not started:
            if not label:
                continue
            started = True
        money: list[Decimal] = []
        note: str | None = None
        for c in range(1, cc):
            cell = g.get((r, c), "")
            if c == note_col:
                if cell and re.fullmatch(r"\d{1,2}[A-Za-z]?", cell):
                    note = cell
                continue
            v = parse_money(cell)
            if v is not None:
                money.append(v)
        if not money and not label:
            continue
        # NOTE limitation: current/prior assigned by left-to-right order, correct
        # for fully-populated rows. A row with a blank current but a present prior
        # would mis-assign; flagged for the structuring step to reconcile.
        rows.append(ExtractedRow(
            label=label, note=note,
            current=money[0] if money else None,
            prior=money[1] if len(money) > 1 else None))
    return rows
