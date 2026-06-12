"""Challenge pass over draft checklist rows (drafting-time variant of stage 8).

Sonnet adversarially re-reads each draft row against the verbatim FRS 102
paragraph it cites and attacks five aspects: faithfulness of requirement_text,
trigger logic, direction, severity, and fact-key sanity. Bulk pass -> Batch API.

Output: build/challenge_results.jsonl — one line per row with row_id, verdict
('clean' | 'disputed') and the issues found. Consumed by the review workbook
builder to put disputed rows at the top of the human review queue.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.llm_client import LLMClient
from pipeline.records import read_jsonl

CHALLENGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["clean", "disputed"]},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "aspect": {
                        "type": "string",
                        "enum": ["faithfulness", "trigger", "direction",
                                 "severity", "fact_keys"],
                    },
                    "problem": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["aspect", "problem", "suggestion"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["verdict", "issues"],
    "additionalProperties": False,
}

CHALLENGE_SYSTEM = """\
You are an adversarial reviewer of draft disclosure-checklist rows for a UK
FRS 102 accounts reviewer (single UK companies, full FRS 102). You are given
the VERBATIM text of an FRS 102 paragraph and ONE draft checklist row derived
from it. Your job is to attack the row. Re-read the paragraph text carefully —
do not rely on memory of FRS 102.

Attack each aspect:
- faithfulness: does requirement_text accurately restate what THIS paragraph
  requires — nothing imported, omitted, overstated or understated?
- trigger: is trigger_type right (always / conditional / encouraged), and does
  trigger_condition capture the actual condition in the paragraph?
- direction: 'missing' = flag when required but absent; 'untriggered' = flag
  when disclosed without the trigger applying; 'both'. Is the choice right?
- severity: 'statutory' where the requirement is materiality-blind company law
  OR restates / is directly underpinned by a Companies Act / Regulations
  requirement; 'standard-material' for normal FRS 102 requirements;
  'standard-immaterial-candidate' only where routinely immaterial.
- fact_keys: are the trigger facts resolvable from a set of accounts and
  correctly used in the condition?

Verdict 'clean' ONLY if every aspect is defensible. If anything is wrong,
doubtful or indefensible, verdict 'disputed' with one issue per problem.
Be specific and brief; suggestions must be actionable edits. Do not invent
problems — a clean row is a valid outcome.
"""


def load_rows() -> list[dict]:
    rows = []
    for path in sorted(Path("build").glob("section_*_rows.jsonl")):
        section = path.stem.removeprefix("section_").removesuffix("_rows")
        with path.open(encoding="utf-8") as fh:
            for n, line in enumerate(fh):
                if line.strip():
                    row = json.loads(line)
                    row["_section"] = section
                    row["_row_id"] = f"{section}-{n:03d}"
                    rows.append(row)
    return rows


def paragraph_text(reference: str, edition: str,
                   recs_2022: dict, recs_2024: dict) -> str:
    if edition == "PR2024":
        rec = recs_2024.get(reference) or recs_2022.get(reference)
    else:
        rec = recs_2022.get(reference) or recs_2024.get(reference)
    return rec.text if rec else "[paragraph text not found]"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="build/challenge_results.jsonl")
    args = ap.parse_args()

    recs_2022 = {r.reference: r for r in read_jsonl("build/frs102_2022.jsonl")}
    recs_2024 = {r.reference: r for r in read_jsonl("build/frs102_2024.jsonl")}
    rows = load_rows()
    print(f"challenging {len(rows)} draft rows", flush=True)

    items: list[tuple[str, str]] = []
    for row in rows:
        para = paragraph_text(row["reference"], row["edition"], recs_2022, recs_2024)
        user = (
            f"FRS 102 paragraph {row['reference']} "
            f"(edition applicability: {row['edition']}), verbatim:\n\n{para}\n\n"
            "Draft checklist row to challenge:\n"
            + json.dumps({k: row[k] for k in
                          ("requirement_text", "trigger_type", "trigger_condition",
                           "trigger_facts", "direction", "severity")},
                         ensure_ascii=False, indent=2))
        items.append((row["_row_id"].replace(".", "_"), user))

    client = LLMClient()
    results = client.complete_json_batch("challenge", CHALLENGE_SYSTEM, items,
                                         CHALLENGE_SCHEMA, max_tokens=1000)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    verdicts: Counter[str] = Counter()
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            cid = row["_row_id"].replace(".", "_")
            res = results.get(cid, {"_error": "missing"})
            if "_error" in res:
                verdicts["error"] += 1
                payload = {"row_id": row["_row_id"], "verdict": "error",
                           "issues": [], "error": res["_error"]}
            else:
                verdicts[res["verdict"]] += 1
                payload = {"row_id": row["_row_id"], "verdict": res["verdict"],
                           "issues": res["issues"]}
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print("verdicts:", dict(verdicts), flush=True)
    print(client.usage_summary(), flush=True)


if __name__ == "__main__":
    main()
