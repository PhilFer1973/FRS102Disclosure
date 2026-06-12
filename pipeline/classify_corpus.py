"""Full-corpus para_type classification (Phase 0 step 4).

Classifies every parsed FRS 102 paragraph record in both editions via the
Message Batches API (Haiku, 50% batch pricing) using the 5-way taxonomy in
pipeline.draft_checklist. Output: build/para_types.jsonl, one row per
(edition, reference) with para_type + rationale. This file later feeds the
paragraphs table load and is consumed by draft_checklist instead of inline
classification calls.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.draft_checklist import CLASSIFY_SCHEMA, CLASSIFY_SYSTEM
from pipeline.llm_client import LLMClient
from pipeline.records import read_jsonl

EDITION_TAGS = {"pre-PR2024": "pre", "PR2024": "pr24"}


def _custom_id(edition: str, reference: str) -> str:
    # custom_id charset is [A-Za-z0-9_-]; references contain dots only otherwise
    return f"{EDITION_TAGS[edition]}-{reference.replace('.', '_')}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="build/para_types.jsonl")
    args = ap.parse_args()

    items: list[tuple[str, str]] = []
    index: dict[str, tuple[str, str]] = {}  # custom_id -> (edition, reference)
    for fn in ("build/frs102_2022.jsonl", "build/frs102_2024.jsonl"):
        for r in read_jsonl(fn):
            cid = _custom_id(r.edition, r.reference)
            index[cid] = (r.edition, r.reference)
            items.append((cid, f"Paragraph {r.reference} of FRS 102:\n\n{r.text}"))

    print(f"classifying {len(items)} paragraph records "
          f"({len(items) - len(index)} duplicate ids would be a bug: "
          f"{len(items) == len(index)})", flush=True)

    client = LLMClient()
    results = client.complete_json_batch("classify", CLASSIFY_SYSTEM, items,
                                         CLASSIFY_SCHEMA, max_tokens=300)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    counts: Counter[str] = Counter()
    with out.open("w", encoding="utf-8") as fh:
        for cid, (edition, reference) in index.items():
            res = results.get(cid, {"_error": "missing"})
            if "_error" in res:
                errors += 1
                row = {"edition": edition, "reference": reference,
                       "para_type": None, "error": res["_error"]}
            else:
                counts[res["para_type"]] += 1
                row = {"edition": edition, "reference": reference,
                       "para_type": res["para_type"], "rationale": res["rationale"]}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("para_type distribution:", dict(counts.most_common()), flush=True)
    print(f"errors: {errors}", flush=True)
    print(client.usage_summary(), flush=True)


if __name__ == "__main__":
    main()
