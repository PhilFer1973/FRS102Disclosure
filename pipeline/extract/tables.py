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

    # Money columns: those (excluding label col 0 and the note col) where some
    # row holds a parseable figure. In the UK vertical format each year occupies
    # an equal block of columns (inner + outer), so split the money columns into
    # two halves: left = current year, right = prior year. This assigns blank
    # current/prior cells correctly (where left-to-right order would not).
    money_cols = sorted(
        c for c in range(1, cc) if c != note_col
        and any(parse_money(g.get((r, c), "")) is not None for r in range(rc)))
    half = len(money_cols) // 2
    even = len(money_cols) % 2 == 0 and half > 0
    cur_cols = money_cols[:half] if even else money_cols
    pri_cols = money_cols[half:] if even else money_cols

    def first_money(cols, row):
        for c in cols:
            v = parse_money(g.get((row, c), ""))
            if v is not None:
                return v
        return None

    rows: list[ExtractedRow] = []
    started = False  # skip the leading header band (year / '£' rows)
    for r in range(rc):
        label = g.get((r, 0), "")
        if not started:
            if not label:
                continue
            started = True
        note = g.get((r, note_col), "") if note_col is not None else ""
        note = note if note and re.fullmatch(r"\d{1,2}[A-Za-z]?", note) else None
        if even:
            current, prior = first_money(cur_cols, r), first_money(pri_cols, r)
        else:  # odd/degenerate layout: fall back to left-to-right order
            vals = [parse_money(g.get((r, c), "")) for c in money_cols]
            vals = [v for v in vals if v is not None]
            current = vals[0] if vals else None
            prior = vals[1] if len(vals) > 1 else None
        if current is None and prior is None and not label:
            continue
        rows.append(ExtractedRow(label=label, note=note,
                                 current=current, prior=prior))
    return rows
