"""Fact-profile builder (pipeline stage 4): resolve the trigger facts the active
checklist rules need, from the extracted accounts.

Haiku-assisted (CLAUDE.md routing). Each fact resolves to true / false / a
specific enum value, or 'unknown' — the model is told NOT to guess, so anything
unevidenced stays unresolved and the checklist engine routes that requirement to
the question queue. Each resolution records value, confidence and reasoning
(method='llm'); the value's source is the condensed accounts context below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.llm_client import LLMClient, LLMTruncationError
from pipeline.validate.fs_model import FinancialStatements

FACT_SCHEMA = {
    "type": "object",
    "properties": {
        "resolutions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},      # 'true'|'false'|'unknown'|<enum>
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["key", "value", "confidence", "reasoning"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["resolutions"],
    "additionalProperties": False,
}

FACT_SYSTEM = """\
You resolve facts about a single UK company's FRS 102 financial statements, for
a disclosure-checklist engine. You are given the accounts (primary statements
with figures, notes present, entity info) and a list of facts, each a key with a
short description.

For each fact, determine its value ONLY from the accounts provided:
- boolean facts: answer exactly 'true' or 'false'.
- enum facts: answer the specific value.
- if the accounts do not evidence the fact either way: answer 'unknown'.

These are a COMPLETE set of filed financial statements. Treat them as complete:
a set of accounts discloses what exists, so the ABSENCE of any related line item,
note or mention is itself evidence.

- PRESENCE facts (keys like 'has_...', 'is_...', 'uses_...', 'applies_...'): if
  there is no line, note or mention supporting them, resolve to 'false' — NOT
  'unknown'. E.g. no associates note -> has_investments_in_associates = false;
  no lease commitments -> is_lessee = false; no share-based-payment note ->
  has_share_based_payment_arrangements = false. If the item IS present (a
  'Creditors: amounts falling due within one year' line, an employees note giving
  an average number, a goodwill/investments line), resolve to 'true' / the value.
- STATUS facts ARE disclosed in the narrative — READ them, do not punt to the
  reviewer: whether the entity is a qualifying entity, takes the consolidation or
  cash-flow-statement exemption, is a small entity / applies Section 1A, the
  going-concern basis of preparation, and any prior-period restatement (look for
  'qualifying entity', 'exemption', 'consolidat', 'going concern', 'as restated').
  Resolve these from the disclosure when it is present.
- Reserve 'unknown' ONLY for things that genuinely are not in the accounts even
  when true — management intentions and undisclosed going-concern doubts. Those,
  and only those, go to the reviewer.

Give a one-line reasoning grounded in the accounts and a confidence 0 to 1.
"""


@dataclass
class FactResolution:
    key: str
    value: str
    confidence: float
    reasoning: str
    method: str = "llm"


_STATUS_TERMS = ("qualifying entity", "exempt", "consolidat", "going concern",
                 "as restated", "small compan", "section 1a", "statement of cash",
                 "cash flow", "merger", "associate", "joint venture",
                 "dividend", "employee")


def _disclosure_excerpt(narrative: str, window: int = 600, cap: int = 14000) -> str:
    """Compact excerpt of the prose around the status-disclosure terms, merged, so
    the resolver sees the qualifying-entity / exemption / going-concern statements
    wherever they appear without shipping the whole back-half narrative."""
    low = narrative.lower()
    spans: list[tuple[int, int]] = []
    for term in _STATUS_TERMS:
        start = 0
        while (i := low.find(term, start)) >= 0:
            spans.append((max(0, i - window), i + window))
            start = i + len(term)
    if not spans:
        return narrative[:cap]
    spans.sort()
    merged = [spans[0]]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return "\n…\n".join(narrative[s:e] for s, e in merged)[:cap]


def accounts_context(fs: FinancialStatements, note_titles: list[str],
                     edition: str, narrative: str = "") -> str:
    out = [f"Entity: {fs.entity_name}", f"Period end: {fs.period_end}",
           f"FRS 102 edition: {edition}", ""]
    if narrative.strip():
        # The status disclosures (qualifying entity, exemptions, going concern,
        # restatement) sit anywhere in the prose — often mid-document — so feed a
        # TARGETED excerpt around those terms, not a blind prefix.
        out.append("== Accounts narrative (disclosures) ==")
        out.append(_disclosure_excerpt(narrative))
        out.append("")
    for name, stmt in fs.statements.items():
        out.append(f"== {name.replace('_', ' ')} ==")
        for it in stmt.items:
            cur = "" if it.current is None else f"{it.current:,}"
            out.append(f"  {it.label}: {cur}")
        out.append("")
    # Note line items too (not just titles) — so facts evidenced in the notes
    # (e.g. the average number of employees, creditor splits) can be resolved
    # without asking the reviewer.
    notes = getattr(fs, "notes", {}) or {}
    if notes:
        out.append("== Notes ==")
        for note in notes.values():
            head = f"  Note {getattr(note, 'number', '')}".rstrip()
            out.append(head)
            for it in getattr(note, "items", []) or []:
                cur = "" if it.current is None else f"{it.current:,}"
                out.append(f"    {it.label}: {cur}")
    elif note_titles:
        out.append("== Notes present ==")
        out += [f"  {t}" for t in note_titles]
    return "\n".join(out)


# Judgement confirms that always go to the reviewer, never auto-defaulted by the
# presence backstop (they need a human "confirming that…" even when nothing in the
# accounts contradicts them).
ALWAYS_ASK = frozenset({
    "has_key_estimation_uncertainties",
    "has_going_concern_material_uncertainties",
    "not_going_concern",
    "has_material_prior_period_error",
})


_CF_STATEMENT_RE = re.compile(
    r"cash (?:flows? from|generated from|used in)\s+(?:operating|investing|financing)"
    r"|net cash (?:from|used)|(?:investing|financing) activities", re.IGNORECASE)


def compute_cashflow_presence(narrative: str) -> dict[str, bool]:
    """Detect a real statement of cash flows from its line items, rather than
    trusting the model — which confuses 'exempt from preparing a statement of cash
    flows' with actually presenting one. No such line items -> not presented."""
    return {"presents_cash_flow_statement": bool(_CF_STATEMENT_RE.search(narrative or ""))}


def compute_statement_presence(fs: FinancialStatements, narrative: str) -> dict[str, bool]:
    """Which primary statements are actually present, from the extraction and the
    headings — so statement-presence rules (complete set, SOCE content) aren't
    flagged 'missing' when the statement is plainly there. General, not entity-
    specific. Cash flow statement is handled separately (exemption-aware)."""
    low = (narrative or "").lower()
    return {
        "presents_income_statement": "income" in fs.statements
            or "profit and loss account" in low or "income statement" in low
            or "statement of comprehensive income" in low,
        "presents_balance_sheet": "balance_sheet" in fs.statements
            or "balance sheet" in low or "statement of financial position" in low,
        "presents_statement_of_changes_in_equity":
            "statement of changes in equity" in low,
        "presents_notes": bool(getattr(fs, "notes", {}) or {})
            or "notes to the financial statements" in low
            or "notes to the accounts" in low,
    }


_DEPARTURE_RE = re.compile(
    r"depart(?:ed|ure|ing)\s+from|true and fair override|override of (?:a|the) requirement",
    re.IGNORECASE)


def compute_departure_facts(narrative: str) -> dict[str, bool]:
    """A FRS 102 / company-law departure (true-and-fair override) is rare and is
    ALWAYS explicitly worded. Without that wording there is no departure — so don't
    let the resolver read an ordinary prior-period RESTATEMENT (10.21, correcting an
    error) as a departure (3.6). No departure language -> both departure facts
    false. General; if the wording IS present, leave it to the resolver."""
    if _DEPARTURE_RE.search(narrative or ""):
        return {}
    return {"has_prior_period_departure_affecting_current_amounts": False,
            "has_departure_from_company_law_accounting_principles": False}


_EMPLOYEES_RE = re.compile(
    r"average\s+(?:monthly\s+)?number\s+of\s+(?:persons\s+employed|employees|staff|persons)",
    re.IGNORECASE)


def compute_employees_fact(narrative: str) -> dict[str, bool]:
    """Read the CA06 s411 average-number-of-employees disclosure and settle the
    >250 threshold, so it isn't asked. Take the largest non-year number in the
    text right after the phrase (the total headcount)."""
    m = _EMPLOYEES_RE.search(narrative or "")
    if not m:
        return {}
    tail = narrative[m.end(): m.end() + 300]
    # Only read the headcount block — stop at the next note heading / page marker /
    # Docusign id, so following figures (interest, envelope ids) don't contaminate.
    cut = re.search(r"\n\s*\d+\.\s|\bPage\b|Docusign", tail)
    if cut:
        tail = tail[:cut.start()]
    nums = [int(t.replace(",", "")) for t in re.findall(r"\d[\d,]*", tail)]
    nums = [n for n in nums if not (2000 <= n <= 2100) and n < 100000]  # drop years/£
    return {"average_employees_gt_250": max(nums) > 250} if nums else {}


def compute_size_facts(fs: FinancialStatements) -> dict[str, bool]:
    """Settle entity-size / framework facts deterministically where the figures
    clearly exceed the CA06 thresholds — failing two of the three tests means the
    entity is NOT in that size band, so the band's regime cannot apply. Returns {}
    for anything borderline (those still read the accounts). The accounting
    framework is also always disclosed, so this only needs to settle the clear
    'too big to be micro / small' cases.

    Thresholds (gross = balance-sheet total): micro £632k / £316k; small £10.2m /
    £5.1m. Use AND on turnover and gross so the entity has clearly failed two of
    the three tests before we rule the band out."""
    from decimal import Decimal

    from pipeline.engine.materiality import extract_benchmarks
    b = extract_benchmarks(fs)
    turnover, gross = b.get("turnover"), b.get("gross_assets")
    if turnover is None or gross is None:
        return {}
    out: dict[str, bool] = {}
    if abs(turnover) > Decimal("632000") and gross > Decimal("316000"):
        out.update(is_micro_entity=False, applies_FRS105=False)
    if abs(turnover) > Decimal("10200000") and gross > Decimal("5100000"):
        out.update(is_small_entity=False, applies_section_1A=False)
    return out


def build_fact_profile(facts_needed: set[str], registry: dict[str, dict],
                       fs: FinancialStatements, note_titles: list[str],
                       edition: str, client: LLMClient, batch: int = 15,
                       narrative: str = ""
                       ) -> tuple[dict[str, object], list[FactResolution]]:
    context = accounts_context(fs, note_titles, edition, narrative)
    profile: dict[str, object] = {}
    resolutions: list[FactResolution] = []

    def resolve(chunk: list[str]) -> list[dict]:
        """Resolve a chunk of facts; if the model's JSON overflows the output
        ceiling, split the chunk and retry, so a large filing self-heals instead
        of dying on a truncated parse. A single fact that still overflows is a
        genuine error and propagates."""
        listing = "\n".join(
            f"- {k}: {registry.get(k, {}).get('description', k)}" for k in chunk)
        user = f"ACCOUNTS:\n{context}\n\nFACTS TO RESOLVE:\n{listing}"
        try:
            return client.complete_json("facts", FACT_SYSTEM, user, FACT_SCHEMA,
                                        max_tokens=8000)["resolutions"]
        except LLMTruncationError:
            if len(chunk) <= 1:
                raise
            mid = len(chunk) // 2
            return resolve(chunk[:mid]) + resolve(chunk[mid:])

    keys = sorted(facts_needed)
    for start in range(0, len(keys), batch):
        chunk = keys[start:start + batch]
        for r in resolve(chunk):
            resolutions.append(FactResolution(r["key"], r["value"],
                                              r["confidence"], r["reasoning"]))
            v = r["value"].strip().lower()
            if v == "true":
                profile[r["key"]] = True
            elif v == "false":
                profile[r["key"]] = False
            elif v == "unknown":
                continue                      # leave unresolved
            else:
                profile[r["key"]] = r["value"]   # enum value
    # Deterministic reads/computations override the model where they're clear-cut.
    computed = {**compute_size_facts(fs), **compute_employees_fact(narrative),
                **compute_cashflow_presence(narrative),
                **compute_statement_presence(fs, narrative),
                **compute_departure_facts(narrative)}
    for k, val in computed.items():
        profile[k] = val
        resolutions.append(FactResolution(k, str(val).lower(), 1.0,
                                          "read/computed from the accounts",
                                          method="computed"))
    # Backstop (Phil's rule): a presence fact ('has_...') or a vague '..._relevant'
    # fact the model left unresolved means the accounts show no sign of it — treat
    # as false (not-present-and-not-disclosed = ignore), so it isn't asked. The
    # genuine judgement confirms are exempt and still go to the reviewer.
    for f in facts_needed:
        if f in profile or f in ALWAYS_ASK:
            continue
        if (f.startswith(("has_", "uses_")) or f.endswith("_relevant")):
            profile[f] = False
            resolutions.append(FactResolution(f, "false", 0.6,
                                              "no sign in the accounts (absence)",
                                              method="backstop"))
    # The judgement confirms always go to the reviewer, even if the accounts
    # address them — the reviewer may know of something the accounts don't (e.g.
    # going-concern doubts). Drop them from the resolved profile so they surface.
    for k in ALWAYS_ASK:
        profile.pop(k, None)
    return profile, resolutions
