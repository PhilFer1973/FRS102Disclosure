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
    current_confidence: float | None = None   # Azure OCR confidence per figure
    prior_confidence: float | None = None


WordSpans = list[tuple[int, int, float]]


def word_spans(layout: dict) -> WordSpans:
    """(offset, end, confidence) for every recognised word, for mapping a table
    cell back to its OCR confidence via the shared character-span index."""
    out: WordSpans = []
    for page in layout.get("pages", []) or []:
        for w in page.get("words", []) or []:
            sp = w.get("span") or {}
            if sp.get("offset") is not None and w.get("confidence") is not None:
                out.append((sp["offset"], sp["offset"] + sp.get("length", 0),
                            w["confidence"]))
    return sorted(out)


def _cell_confidence(spans: list[dict] | None, ws: WordSpans) -> float | None:
    confs = []
    for cs in spans or []:
        c0 = cs.get("offset")
        if c0 is None:
            continue
        c1 = c0 + cs.get("length", 0)
        confs += [conf for w0, w1, conf in ws if w0 < c1 and w1 > c0]
    return min(confs) if confs else None


def _grid(table: dict):
    content: dict[tuple[int, int], str] = {}
    spans: dict[tuple[int, int], list[dict]] = {}
    for c in table["cells"]:
        key = (c["rowIndex"], c["columnIndex"])
        content[key] = (c.get("content") or "").replace("\n", " ").strip()
        spans[key] = c.get("spans") or []
    return content, spans, table["rowCount"], table["columnCount"]


def _note_column(g: dict, cc: int) -> int | None:
    """The note-reference column, identified by its header ('Note', 'Notes',
    'Note(s)', 'Ref'…). Must be excluded from money parsing, else single-digit
    note references are read as figures and shift every value on the row."""
    for col in range(cc):
        h = g.get((0, col), "").strip().lower().rstrip(".")
        if h.startswith("note") or h in ("ref", "refs", "reference"):
            return col
    return None


def extract_statement(table: dict, ws: WordSpans | None = None) -> list[ExtractedRow]:
    """Extract (label, note, current, prior) rows from a two-period statement
    table. Header/blank rows yield no usable row and are skipped, but a blank
    label with figures (an unlabelled subtotal) is kept with label ''. When
    `ws` (word spans) is given, the current figure carries its OCR confidence."""
    g, spans, rc, cc = _grid(table)
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
                return v, c
        return None, None

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
        cur_col = pri_col = None
        if even:
            current, cur_col = first_money(cur_cols, r)
            prior, pri_col = first_money(pri_cols, r)
        else:  # odd/degenerate layout: fall back to left-to-right order
            found = [(parse_money(g.get((r, c), "")), c) for c in money_cols]
            found = [(v, c) for v, c in found if v is not None]
            current, cur_col = found[0] if found else (None, None)
            prior, pri_col = found[1] if len(found) > 1 else (None, None)
        if current is None and prior is None and not label:
            continue
        cc_conf = (_cell_confidence(spans.get((r, cur_col)), ws)
                   if ws is not None and cur_col is not None else None)
        pc_conf = (_cell_confidence(spans.get((r, pri_col)), ws)
                   if ws is not None and pri_col is not None else None)
        rows.append(ExtractedRow(label=label, note=note, current=current,
                                 prior=prior, current_confidence=cc_conf,
                                 prior_confidence=pc_conf))
    return rows
