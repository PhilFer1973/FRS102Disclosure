"""Full review pipeline: PDF -> issues register.

  uv run python -m cli.review_pdf --layout-json build/layout/FC.layout.json \
      --entity "Four Communications Limited" --period-end 2024-12-31 --edition pre-PR2024

PDF/cached Layout -> extract + structure -> numerical gate -> load active rules
-> resolve the facts they need -> checklist engine (which disclosures apply) ->
persist engagement/run/findings -> summary. Document extraction is the only
paid-per-page step; structuring + fact resolution are a few LLM calls.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from db import store
from pipeline.engine.checklist import required_facts, run_checklist
from pipeline.engine.presence import check_presence, gather_narrative
from pipeline.extract.structure import _note_headings, assemble
from pipeline.facts.builder import build_fact_profile
from pipeline.intake.router import Accepted
from pipeline.llm_client import LLMClient
from pipeline.validate.checks import validate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--layout-json")
    src.add_argument("--pdf")
    ap.add_argument("--entity", required=True)
    ap.add_argument("--period-end", required=True)
    ap.add_argument("--edition", choices=["pre-PR2024", "PR2024"], default="pre-PR2024")
    ap.add_argument("--no-persist", action="store_true")
    args = ap.parse_args()

    if args.layout_json:
        layout = json.loads(Path(args.layout_json).read_text(encoding="utf-8"))
    else:
        from pipeline.extract.pdf_layout import analyze_pdf
        result = analyze_pdf(args.pdf)
        layout = result.as_dict() if hasattr(result, "as_dict") else result

    client = LLMClient()
    fs = assemble(layout, client, args.entity, args.period_end)
    numerical = validate(fs)
    print(f"extracted {sum(len(s.items) for s in fs.statements.values())} lines across "
          f"{len(fs.statements)} statements; numerical gate: {len(numerical)} findings")

    reqs = store.get_active_requirements(args.edition)
    registry = store.get_fact_registry()
    note_titles = [f"{h['number']}. {h['title']}" for h in _note_headings(layout)]
    needed = required_facts(reqs, args.edition)
    print(f"active rules in scope: {len(reqs)}; facts to resolve: {len(needed)}")

    profile, resolutions = build_fact_profile(needed, registry, fs, note_titles,
                                              args.edition, client)
    results = run_checklist(reqs, profile, args.edition)
    by_outcome: dict[str, int] = {}
    for r in results:
        by_outcome[r.outcome] = by_outcome.get(r.outcome, 0) + 1
    print(f"resolved {len(profile)}/{len(needed)} facts; checklist outcomes: {by_outcome}")

    applicable = [r for r in results if r.outcome == "applicable"
                  and r.requirement.direction in ("missing", "both")]

    # Presence detection: of the required disclosures, which are actually present?
    presence = check_presence(applicable, gather_narrative(layout), client)
    missing = [p for p in presence if p.status == "absent"]
    unclear = [p for p in presence if p.status == "unclear"]
    present = [p for p in presence if p.status == "present"]
    print(f"\npresence of {len(applicable)} required disclosures: "
          f"{len(present)} present, {len(missing)} MISSING, {len(unclear)} unclear")
    print(f"\nMISSING required disclosures ({len(missing)}):")
    for p in missing[:15]:
        print(f"  [{p.requirement.requirement.reference}] "
              f"{p.requirement.requirement.requirement_text[:88]}")

    undetermined = [r for r in results if r.outcome == "undetermined"]
    print(f"\n{len(undetermined)} undetermined (-> question queue)")

    if not args.no_persist:
        accepted = Accepted(args.entity, date.fromisoformat("2024-01-01"),
                            date.fromisoformat(args.period_end), args.edition)
        eid = store.create_engagement(accepted)
        rid, seq = store.create_run(eid)
        n_num = store.write_findings(rid, numerical)
        n_chk = store.write_presence_findings(rid, presence)
        store.complete_run(rid)
        print(f"\npersisted engagement {eid}, run {rid}: {n_num} numerical + "
              f"{n_chk} disclosure findings")
    print("\n" + client.usage_summary())


if __name__ == "__main__":
    main()
