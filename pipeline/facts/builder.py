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

Do NOT guess. 'unknown' is the correct answer whenever the provided information
is insufficient — a downstream question will resolve it. Give a one-line
reasoning grounded in the accounts and a confidence between 0 and 1.
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
    if note_titles:
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
