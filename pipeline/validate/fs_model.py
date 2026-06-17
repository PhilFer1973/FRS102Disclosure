"""Typed financial-statements model that the numerical validation gate checks.

Extraction (Phase 1, later) populates this model from PDF/Word/Excel; the
deterministic checks in checks.py operate ONLY on this model — never on raw
documents, and never via an LLM (CLAUDE.md hard rule 1).

Design: a statement is an ordered list of LineItems. A LineItem is either a leaf
(an extracted figure) or derived from other lines via a signed sum
(`derivation`: list of (line_id, sign)). This one construct expresses casting
(all +1 components), subtotals, net assets (assets +1, liabilities -1), reserves
articulation (opening +1, profit +1, dividends -1, ...) and cash-flow movement
(closing -1, opening +1 == net flow). Cross-statement and note->face identities
are expressed as Equality checks between line ids.

Money is Decimal — exact, no float drift. Missing values are None and never
silently coerced to 0 (hard rule 5); a check that needs an absent value emits
an explicit error finding instead.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

Money = Decimal


@dataclass(frozen=True)
class LineItem:
    id: str
    label: str
    current: Money | None = None
    prior: Money | None = None
    # signed components for a derived line; None => leaf (extracted figure)
    derivation: tuple[tuple[str, int], ...] | None = None
    note_ref: str | None = None        # note number this line points to
    source_loc: str | None = None      # page/table/cell provenance from extraction
    current_confidence: float | None = None   # OCR confidence per figure
    prior_confidence: float | None = None

    def confidence_for(self, column: str) -> float | None:
        return self.current_confidence if column == "current" else self.prior_confidence


@dataclass
class Statement:
    name: str                          # 'balance_sheet' | 'income' | 'socie' | 'cash_flow'
    items: list[LineItem] = field(default_factory=list)

    def by_id(self) -> dict[str, LineItem]:
        index: dict[str, LineItem] = {}
        for it in self.items:
            if it.id in index:
                raise ValueError(f"duplicate line id {it.id!r} in {self.name}")
            index[it.id] = it
        return index


@dataclass
class Note:
    number: str
    title: str
    items: list[LineItem] = field(default_factory=list)

    def by_id(self) -> dict[str, LineItem]:
        index: dict[str, LineItem] = {}
        for it in self.items:
            if it.id in index:
                raise ValueError(f"duplicate line id {it.id!r} in note {self.number}")
            index[it.id] = it
        return index


@dataclass(frozen=True)
class Equality:
    """Two line references that must be equal (per column). Used for
    balance-sheet balancing, note->face cross-cast, cash-flow reconciliation."""
    left: str                          # 'statement:line_id' or 'note:number:line_id'
    right: str
    description: str


@dataclass(frozen=True)
class RatioCheck:
    """A line that must equal another line times a rate, within tolerance.
    Covers the ETR reconciliation's 'tax at the standard rate = PBT x rate'
    (the one multiplicative check; everything else is a signed sum)."""
    target: str                        # line ref expected to equal base * rate
    base: str                          # line ref the rate is applied to
    rate: Money                        # e.g. Decimal('0.25')
    description: str


@dataclass
class FinancialStatements:
    entity_name: str
    period_end: str
    rounding_unit: Money = Decimal("1")   # accounts presented to this unit
    statements: dict[str, Statement] = field(default_factory=dict)
    notes: dict[str, Note] = field(default_factory=dict)
    equalities: list[Equality] = field(default_factory=list)
    ratio_checks: list[RatioCheck] = field(default_factory=list)
    has_comparatives: bool = True

    def resolve(self, ref: str) -> LineItem | None:
        """Resolve 'statement:<name>:<line_id>' or 'note:<number>:<line_id>'."""
        parts = ref.split(":")
        if len(parts) != 3:
            raise ValueError(f"malformed reference {ref!r}")
        kind, container, line_id = parts
        if kind == "statement":
            stmt = self.statements.get(container)
            return stmt.by_id().get(line_id) if stmt else None
        if kind == "note":
            note = self.notes.get(container)
            return note.by_id().get(line_id) if note else None
        raise ValueError(f"malformed reference {ref!r}")


def _money(v: str | int | float | None) -> Money | None:
    return None if v is None else Decimal(str(v))


def _line_from_dict(d: dict) -> LineItem:
    deriv = d.get("derivation")
    return LineItem(
        id=d["id"], label=d["label"],
        current=_money(d.get("current")), prior=_money(d.get("prior")),
        derivation=tuple((c[0], int(c[1])) for c in deriv) if deriv else None,
        note_ref=d.get("note_ref"), source_loc=d.get("source_loc"),
        current_confidence=d.get("current_confidence"),
        prior_confidence=d.get("prior_confidence"))


def from_dict(d: dict) -> FinancialStatements:
    """Deserialize an FS model from plain JSON (the extraction output contract).
    Money values may be strings or numbers; stored as Decimal."""
    return FinancialStatements(
        entity_name=d["entity_name"], period_end=d["period_end"],
        rounding_unit=_money(d.get("rounding_unit", 1)) or Decimal(1),
        has_comparatives=d.get("has_comparatives", True),
        statements={name: Statement(name, [_line_from_dict(x) for x in s["items"]])
                    for name, s in d.get("statements", {}).items()},
        notes={num: Note(num, n["title"], [_line_from_dict(x) for x in n["items"]])
               for num, n in d.get("notes", {}).items()},
        equalities=[Equality(e["left"], e["right"], e["description"])
                    for e in d.get("equalities", [])],
        ratio_checks=[RatioCheck(r["target"], r["base"], _money(r["rate"]),
                                 r["description"]) for r in d.get("ratio_checks", [])])


def load_fs_json(path: str | Path) -> FinancialStatements:
    return from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
