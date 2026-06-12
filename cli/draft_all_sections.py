"""Phase 0 step 5 driver: draft checklist rows for every in-scope section.

Order: core sections ascending (1, 1A, 2, 2A, 3, 5..35 — 4 already piloted),
then section-appendix families (1AA, 1AB, 1AC, 1AE, 12A, 19A, 21A, 23A, 34A).
Ascending order matters: the fact-key registry accumulates across sections.

Excluded from drafting (still classified for the paragraphs table):
- 4     already drafted in the pilot
- 1AD   Republic of Ireland small-entity disclosures (scope: UK companies)
- PBE*  public benefit entity paragraphs (scope: charities rejected by router)

Continues past per-section failures and reports them at the end.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from pipeline.draft_checklist import run_section

DRAFT_EXCLUDED = {"4", "1AD"}


def pick_sections(families: list[str]) -> list[str]:
    """In-scope families in drafting order (core sections, then appendices)."""
    def core_key(fam: str) -> tuple[int, str]:
        digits = "".join(c for c in fam if c.isdigit())
        return (int(digits), fam)

    in_scope = [f for f in families
                if f not in DRAFT_EXCLUDED and not f.startswith("PBE")]
    core = sorted((f for f in in_scope if len(f) <= 2 or f == "1A"),
                  key=core_key)
    appendices = sorted((f for f in in_scope if f not in core), key=core_key)
    return core + appendices


def main() -> None:
    families = sorted({json.loads(line)["family"]
                       for line in Path("build/edition_diff.jsonl").open(encoding="utf-8")
                       if line.strip()})
    sections = pick_sections(families)
    print(f"drafting {len(sections)} sections: {', '.join(sections)}", flush=True)

    total_cost = 0.0
    failures: list[str] = []
    for n, sec in enumerate(sections, 1):
        label = f"{int(sec):02d}" if sec.isdigit() else sec
        print(f"\n=== [{n}/{len(sections)}] Section {sec} ===", flush=True)
        try:
            client = run_section(sec, Path(f"review/section_{label}_draft.md"),
                                 Path(f"build/section_{label}_rows.jsonl"))
            total_cost += client.total_cost_usd()
            print(f"section {sec} done; cumulative drafting cost ${total_cost:.2f}",
                  flush=True)
        except Exception:
            failures.append(sec)
            traceback.print_exc()
            print(f"section {sec} FAILED — continuing", flush=True)

    print(f"\n==== DONE: {len(sections) - len(failures)}/{len(sections)} sections, "
          f"total drafting cost ${total_cost:.2f} ====", flush=True)
    if failures:
        print("failed sections:", ", ".join(failures), flush=True)


if __name__ == "__main__":
    main()
