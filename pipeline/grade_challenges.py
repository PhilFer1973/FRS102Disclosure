"""Grade challenge issues by materiality (Haiku, Batch API).

The challenge pass disputed 480/545 rows — correct but unprioritised. This pass
grades each issue: 'material' if, left uncorrected, it would change what the
checklist flags on a real engagement (wrong trigger logic, wrong direction,
wrong severity tier, requirement misstated); 'minor' if it is wording precision,
completeness of citation, or stylistic improvement.

Rewrites build/challenge_results.jsonl in place with materiality per issue and
a row-level grade: 'material' | 'minor' | 'clean'.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pipeline.llm_client import LLMClient

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "gradings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "materiality": {"type": "string", "enum": ["material", "minor"]},
                },
                "required": ["index", "materiality"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["gradings"],
    "additionalProperties": False,
}

GRADE_SYSTEM = """\
You grade review issues raised against draft disclosure-checklist rows
(FRS 102, UK). For each numbered issue decide:

- material: left uncorrected, the row would misbehave on a real engagement —
  it would fire when it should not, fail to fire when it should, point at the
  wrong condition or direction, sit in the wrong severity tier, or assert a
  requirement the paragraph does not impose.
- minor: the row would still behave correctly; the issue is precision of
  wording, completeness of description, naming style, or a suggestion to
  also-cover something adjacent.

Grade every issue. When genuinely unsure, grade material.
"""


def main() -> None:
    path = Path("build/challenge_results.jsonl")
    results = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]

    items: list[tuple[str, str]] = []
    for r in results:
        if r["verdict"] != "disputed" or not r["issues"]:
            continue
        listing = "\n".join(
            f"{n}. [{i['aspect']}] {i['problem']} Suggestion: {i['suggestion']}"
            for n, i in enumerate(r["issues"]))
        items.append((r["row_id"].replace(".", "_"),
                      f"Issues raised against one checklist row:\n\n{listing}"))

    client = LLMClient()
    graded = client.complete_json_batch("classify", GRADE_SYSTEM, items,
                                        GRADE_SCHEMA, max_tokens=500)

    counts: Counter[str] = Counter()
    for r in results:
        cid = r["row_id"].replace(".", "_")
        if r["verdict"] != "disputed" or not r["issues"]:
            r["grade"] = "clean" if r["verdict"] == "clean" else r["verdict"]
        elif cid in graded and "_error" not in graded[cid]:
            by_index = {g["index"]: g["materiality"]
                        for g in graded[cid]["gradings"]}
            for n, issue in enumerate(r["issues"]):
                issue["materiality"] = by_index.get(n, "material")
            r["grade"] = ("material" if any(i["materiality"] == "material"
                                            for i in r["issues"]) else "minor")
        else:
            r["grade"] = "material"  # grading failed -> keep at top of queue
        counts[r["grade"]] += 1

    with path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("row grades:", dict(counts.most_common()), flush=True)
    print(client.usage_summary(), flush=True)


if __name__ == "__main__":
    main()
