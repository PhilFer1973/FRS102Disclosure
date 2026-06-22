"""Fact-profile builder (pipeline stage 4): resolve the trigger facts the active
checklist rules need, from the extracted accounts.

Haiku-assisted (CLAUDE.md routing). Each fact resolves to true / false / a
specific enum value, or 'unknown' — the model is told NOT to guess, so anything
unevidenced stays unresolved and the checklist engine routes that requirement to
the question queue. Each resolution records value, confidence and reasoning
(method='llm'); the value's source is the condensed accounts context below.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.llm_client import LLMClient
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
- Reserve 'unknown' ONLY for facts that genuinely would not be visible in the
  accounts even when true: group membership / qualifying-entity or consolidation
  status, exemptions the entity has chosen to claim, management intentions, and
  going-concern uncertainties. Those go to the reviewer.

Give a one-line reasoning grounded in the accounts and a confidence 0 to 1.
"""


@dataclass
class FactResolution:
    key: str
    value: str
    confidence: float
    reasoning: str
    method: str = "llm"


def accounts_context(fs: FinancialStatements, note_titles: list[str],
                     edition: str) -> str:
    out = [f"Entity: {fs.entity_name}", f"Period end: {fs.period_end}",
           f"FRS 102 edition: {edition}", ""]
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


def build_fact_profile(facts_needed: set[str], registry: dict[str, dict],
                       fs: FinancialStatements, note_titles: list[str],
                       edition: str, client: LLMClient, batch: int = 30
                       ) -> tuple[dict[str, object], list[FactResolution]]:
    context = accounts_context(fs, note_titles, edition)
    profile: dict[str, object] = {}
    resolutions: list[FactResolution] = []
    keys = sorted(facts_needed)
    for start in range(0, len(keys), batch):
        chunk = keys[start:start + batch]
        listing = "\n".join(
            f"- {k}: {registry.get(k, {}).get('description', k)}" for k in chunk)
        user = f"ACCOUNTS:\n{context}\n\nFACTS TO RESOLVE:\n{listing}"
        res = client.complete_json("facts", FACT_SYSTEM, user, FACT_SCHEMA,
                                   max_tokens=4000)
        for r in res["resolutions"]:
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
    return profile, resolutions
