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

from dataclasses import dataclass, field
from decimal import Decimal

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


@dataclass
class FinancialStatements:
    entity_name: str
    period_end: str
    rounding_unit: Money = Decimal("1")   # accounts presented to this unit
    statements: dict[str, Statement] = field(default_factory=dict)
    notes: dict[str, Note] = field(default_factory=dict)
    equalities: list[Equality] = field(default_factory=list)
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
