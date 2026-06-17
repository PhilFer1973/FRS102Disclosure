"""Presence detection: is an applicable required disclosure actually IN the
accounts? This delivers the product's headline — required-and-missing.

The checklist engine decides which disclosures are required; this stage reads the
accounts' narrative (notes + accounting policies, from the Azure Layout
paragraphs) and judges, per applicable requirement, whether the specific
disclosure is present / absent / unclear, with an evidence snippet. Applicable +
absent => a missing-disclosure finding; unclear => flag for human confirmation.

LLM-judged (the match between a requirement and free-text disclosure is inherently
fuzzy); requirements are referenced by a short batch index, never the UUID, to
keep the mapping robust.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.engine.checklist import EngineResult
from pipeline.llm_client import LLMClient

PRESENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "status": {"type": "string",
                               "enum": ["present", "absent", "unclear"]},
                    "evidence": {"type": "string"},
                },
                "required": ["index", "status", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

PRESENCE_SYSTEM = """\
You check whether specific disclosures required by FRS 102 are PRESENT in a UK
company's financial statements. You are given the full narrative text of the
accounts (accounting policies and notes) and a numbered list of required
disclosures.

For each, decide:
- present: the accounts actually make this disclosure (the specific required
  information is given, not merely that the topic is mentioned).
- absent: the accounts clearly do not make this disclosure.
- unclear: you cannot tell from the text provided.

Quote a short evidence snippet from the accounts for 'present'. Be rigorous but
fair. When genuinely uncertain, answer 'unclear' — a human verifies. Return one
result per requirement index.
"""


@dataclass
class PresenceResult:
    requirement: EngineResult
    status: str          # 'present' | 'absent' | 'unclear'
    evidence: str


def gather_narrative(layout: dict) -> str:
    return "\n".join(
        (p.get("content") or "").strip()
        for p in layout.get("paragraphs", []) or [] if p.get("content"))


def check_presence(applicable: list[EngineResult], narrative: str,
                   client: LLMClient, batch: int = 20) -> list[PresenceResult]:
    out: list[PresenceResult] = []
    for start in range(0, len(applicable), batch):
        chunk = applicable[start:start + batch]
        listing = "\n".join(
            f"{i}. [{r.requirement.reference}] {r.requirement.requirement_text}"
            for i, r in enumerate(chunk))
        user = (f"ACCOUNTS NARRATIVE:\n{narrative}\n\n"
                f"REQUIRED DISCLOSURES TO CHECK (by index):\n{listing}")
        res = client.complete_json("presence", PRESENCE_SYSTEM, user,
                                   PRESENCE_SCHEMA, max_tokens=4000)
        by_index = {r["index"]: r for r in res["results"]}
        for i, req in enumerate(chunk):
            r = by_index.get(i, {"status": "unclear",
                                 "evidence": "[no response from presence pass]"})
            out.append(PresenceResult(req, r["status"], r["evidence"]))
    return out
