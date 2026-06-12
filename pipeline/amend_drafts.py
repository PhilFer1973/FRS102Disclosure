"""Auto-amend pass: apply challenge findings to produce v2 draft rows.

For each challenge-disputed row, Sonnet (Batch API) re-reads the verbatim
paragraph, the original row and every challenge issue, and returns corrected
row(s) — or zero rows with a drop reason where the challenge showed the row
asserts a requirement the paragraph does not impose. Clean rows pass through
unchanged. The full current fact-key list rides in every request so amendments
reuse keys instead of inventing spellings.

Output (originals are never overwritten):
- build/rows_v2/section_XX_rows.jsonl   v2 rows, carrying _row_id lineage,
                                        amended flag and change_summary
- build/rows_v2/dropped.jsonl           dropped rows with reasons, for human
                                        confirmation — a drop is a proposal,
                                        not a deletion
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.challenge_drafts import load_rows, paragraph_text
from pipeline.draft_checklist import ROW_SCHEMA
from pipeline.llm_client import LLMClient
from pipeline.records import read_jsonl

_ROW_ITEM_SCHEMA = ROW_SCHEMA["properties"]["rows"]["items"]

AMEND_SCHEMA = {
    "type": "object",
    "properties": {
        "rows": ROW_SCHEMA["properties"]["rows"],
        "dropped": {"type": "boolean"},
        "drop_reason": {"type": ["string", "null"]},
        "change_summary": {"type": "string"},
    },
    "required": ["rows", "dropped", "drop_reason", "change_summary"],
    "additionalProperties": False,
}

AMEND_SYSTEM = """\
You correct draft disclosure-checklist rows for a UK FRS 102 accounts reviewer
(single UK companies, full FRS 102). You receive: the VERBATIM FRS 102
paragraph, ONE draft row derived from it, and the issues an adversarial
challenge raised against it. Re-read the paragraph yourself; the challenge can
be wrong — fix only what the paragraph text supports fixing, and say so in
change_summary where you rejected a challenge point.

Return the corrected row(s):
- Usually one corrected row. Split into several only if the paragraph imposes
  clearly separable requirements that the original wrongly merged.
- If the challenge correctly shows the row asserts a requirement the paragraph
  does not impose (or it is out of scope for single UK companies), return
  rows: [] with dropped: true and a drop_reason.
- Field rules: trigger_type always/conditional/encouraged; trigger_condition is
  a boolean expression over snake_case fact keys (null for always/encouraged);
  trigger_facts lists every key used; direction missing/untriggered/both;
  severity statutory (materiality-blind company law OR restates / directly
  underpinned by Companies Act / Regulations requirements) | standard-material
  | standard-immaterial-candidate; review_notes one sentence for the human
  reviewer noting any judgement you made.
- FACT KEYS: reuse keys from the provided registry verbatim wherever
  semantically identical; only coin a new key when none fits.
- change_summary: 1-2 sentences saying what you changed and why (or why you
  kept something the challenge attacked).
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="build/rows_v2")
    args = ap.parse_args()

    recs_2022 = {r.reference: r for r in read_jsonl("build/frs102_2022.jsonl")}
    recs_2024 = {r.reference: r for r in read_jsonl("build/frs102_2024.jsonl")}
    rows = load_rows()
    challenges = {c["row_id"]: c for c in
                  (json.loads(line) for line in
                   Path("build/challenge_results.jsonl").open(encoding="utf-8"))
                  if c}
    all_keys = sorted({k for row in rows for k in row["trigger_facts"]})
    key_block = "Current fact-key registry:\n" + "\n".join(f"- {k}" for k in all_keys)

    items: list[tuple[str, str]] = []
    for row in rows:
        ch = challenges.get(row["_row_id"])
        if not ch or ch.get("verdict") != "disputed" or not ch.get("issues"):
            continue
        para = paragraph_text(row["reference"], row["edition"], recs_2022, recs_2024)
        issues = "\n".join(
            f"- [{i['aspect']}/{i.get('materiality', 'material')}] {i['problem']} "
            f"Suggestion: {i['suggestion']}"
            for i in ch["issues"])
        original = json.dumps({k: row[k] for k in
                               ("requirement_text", "trigger_type", "trigger_condition",
                                "trigger_facts", "direction", "severity",
                                "review_notes")}, ensure_ascii=False, indent=2)
        user = (f"FRS 102 paragraph {row['reference']} "
                f"(edition applicability: {row['edition']}), verbatim:\n\n{para}\n\n"
                f"Original draft row:\n{original}\n\n"
                f"Challenge issues:\n{issues}\n\n{key_block}")
        items.append((row["_row_id"].replace(".", "_"), user))

    print(f"amending {len(items)} disputed rows "
          f"({len(rows) - len(items)} pass through unchanged)", flush=True)
    client = LLMClient()
    results = client.complete_json_batch("draft", AMEND_SYSTEM, items,
                                         AMEND_SCHEMA, max_tokens=2500)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_section: dict[str, list[dict]] = defaultdict(list)
    dropped: list[dict] = []
    stats: Counter[str] = Counter()
    for row in rows:
        cid = row["_row_id"].replace(".", "_")
        base = {k: row[k] for k in ("source", "reference", "edition", "status")}
        res = results.get(cid)
        if res is None or "_error" in (res or {}):
            if cid in results:
                stats["amend-error-kept-v1"] += 1
                row = {**row, "amended": False,
                       "change_summary": f"[amend failed: {res['_error']} — v1 kept]"}
            else:
                stats["clean-passthrough"] += 1
                row = {**row, "amended": False, "change_summary": ""}
            by_section[row["_section"]].append(row)
            continue
        if res["dropped"]:
            stats["dropped"] += 1
            dropped.append({**row, "drop_reason": res["drop_reason"],
                            "change_summary": res["change_summary"]})
            continue
        stats["amended"] += 1
        for n, new_row in enumerate(res["rows"]):
            out_row = {**base, **new_row, "_section": row["_section"],
                       "_row_id": row["_row_id"] + (f"-s{n}" if n else ""),
                       "amended": True, "change_summary": res["change_summary"]}
            by_section[row["_section"]].append(out_row)

    for section, sec_rows in by_section.items():
        with (out_dir / f"section_{section}_rows.jsonl").open("w", encoding="utf-8") as fh:
            for r in sec_rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "dropped.jsonl").open("w", encoding="utf-8") as fh:
        for r in dropped:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_v2 = sum(len(v) for v in by_section.values())
    print(f"v2 rows: {total_v2}; outcomes: {dict(stats.most_common())}", flush=True)
    print(client.usage_summary(), flush=True)


if __name__ == "__main__":
    main()
