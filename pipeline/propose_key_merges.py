"""Propose fact-key merges: cluster semantically-identical keys, one canonical
name per group. Single Sonnet call over the full key list; output feeds the
review workbook's Fact keys sheet as pre-filled suggestions (human confirms)."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.llm_client import LLMClient

SCHEMA = {
    "type": "object",
    "properties": {
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "canonical": {"type": "string"},
                    "members": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["canonical", "members"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["groups"],
    "additionalProperties": False,
}

SYSTEM = """\
You consolidate a fact-key registry for an FRS 102 disclosure checklist.
Keys are snake_case conditions resolvable from a set of UK statutory accounts.

Group keys that denote the SAME underlying fact (different spellings, word
order, abbreviations, or trivially narrower phrasings of one condition).
Pick the clearest, most reusable member as canonical (or coin a better
snake_case name if every member is poor). Do NOT merge keys that are genuinely
different facts, even if related (e.g. has_intangibles vs has_goodwill).
Only output groups with 2+ members; singletons are implicitly kept.
"""


def main() -> None:
    rows_dir = Path("build/rows_v2")
    keys = sorted({k for p in rows_dir.glob("section_*_rows.jsonl")
                   for line in p.open(encoding="utf-8") if line.strip()
                   for k in json.loads(line).get("trigger_facts", [])})
    client = LLMClient()
    result = client.complete_json("draft", SYSTEM,
                                  "Fact keys:\n" + "\n".join(f"- {k}" for k in keys),
                                  SCHEMA, max_tokens=8000)
    out = Path("build/key_merge_proposals.json")
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    merged = sum(len(g["members"]) for g in result["groups"])
    print(f"{len(keys)} keys -> {len(result['groups'])} merge groups "
          f"covering {merged} keys")
    print(client.usage_summary())


if __name__ == "__main__":
    main()
