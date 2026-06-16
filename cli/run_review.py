"""End-to-end CLI runner spine (Phase 1).

intake profile JSON + FS-model JSON  ->  route (scope/edition)  ->  create
engagement + run  ->  numerical validation gate  ->  write findings  ->  summary.

Document extraction (PDF via Azure Document Intelligence; Word/Excel via
python-docx/openpyxl) will produce the FS-model JSON; until those land (Azure
keys + sample files), pass a prepared FS-model JSON with --fs.

  uv run python -m cli.run_review --profile intake.json --fs accounts.json
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from db import store
from pipeline.intake.router import Accepted, IntakeProfile, Rejected, route
from pipeline.validate.checks import validate
from pipeline.validate.fs_model import load_fs_json


def _profile_from_json(path: str) -> IntakeProfile:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return IntakeProfile(
        entity_name=d["entity_name"],
        period_start=date.fromisoformat(d["period_start"]),
        period_end=date.fromisoformat(d["period_end"]),
        framework=d["framework"], entity_type=d["entity_type"],
        is_consolidated=d["is_consolidated"],
        early_adoption_pr2024=d.get("early_adoption_pr2024", False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--profile", required=True, help="intake profile JSON")
    ap.add_argument("--fs", required=True, help="FS-model JSON")
    ap.add_argument("--no-persist", action="store_true",
                    help="run the gate without writing to the database")
    args = ap.parse_args()

    profile = _profile_from_json(args.profile)
    decision = route(profile)
    if isinstance(decision, Rejected):
        print(f"REJECTED [{decision.reason}]: {decision.detail}")
        raise SystemExit(2)
    assert isinstance(decision, Accepted)
    print(f"accepted: {decision.entity_name}, {decision.edition} edition "
          f"({decision.period_start} to {decision.period_end})")

    fs = load_fs_json(args.fs)
    findings = validate(fs)
    errors = [f for f in findings if f.is_error]
    real = [f for f in findings if not f.is_error]
    print(f"numerical gate: {len(real)} findings, {len(errors)} could-not-evaluate")
    for f in findings:
        tag = "ERROR" if f.is_error else f.check_type
        print(f"  [{tag}] {f.location}: {f.description}")

    if args.no_persist:
        return
    engagement_id = store.create_engagement(decision)
    run_id, seq = store.create_run(engagement_id)
    n = store.write_findings(run_id, findings)
    store.complete_run(run_id)
    print(f"persisted: engagement {engagement_id}, run {run_id} (seq {seq}), "
          f"{n} findings written")


if __name__ == "__main__":
    main()
