"""Numerical + formatting gate eval harness.

Measures the deterministic gate against seeded defects:
- false-positive rate: findings on the clean reference accounts (must be 0).
- recall: fraction of seeded defects the gate catches.

Free, fast, deterministic — runnable in CI. The disclosure (presence) recall
eval is a separate, LLM-driven harness (costs per run) added alongside.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.seeds import ALL_SEEDS, PRESENT_NOTES
from pipeline.validate.checks import validate
from pipeline.validate.formatting import check_formatting
from pipeline.validate.fs_model import from_dict

CLEAN = Path(__file__).parent / "clean_accounts.json"


def run_eval(clean_path: Path = CLEAN) -> dict:
    clean = json.loads(clean_path.read_text(encoding="utf-8"))
    fs = from_dict(clean)
    baseline = validate(fs) + check_formatting(fs, PRESENT_NOTES)
    per_seed = []
    for seed in ALL_SEEDS:
        name, findings, predicate = seed(clean)
        per_seed.append((name, predicate(findings)))
    recall = sum(ok for _, ok in per_seed) / len(per_seed)
    return {"false_positives_clean": len(baseline), "recall": recall,
            "seeds": per_seed, "n_seeds": len(per_seed)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clean", default=str(CLEAN))
    args = ap.parse_args()
    r = run_eval(Path(args.clean))
    print(f"clean false positives: {r['false_positives_clean']} (target 0)")
    print(f"recall: {r['recall']:.0%} ({sum(ok for _, ok in r['seeds'])}"
          f"/{r['n_seeds']} seeded defects caught)")
    for name, ok in r["seeds"]:
        print(f"  {'CAUGHT' if ok else 'MISSED':7} {name}")
    if r["false_positives_clean"] or r["recall"] < 1.0:
        raise SystemExit("eval regression")


if __name__ == "__main__":
    main()
