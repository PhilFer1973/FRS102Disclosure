"""Adaptive interview selector.

Given the data-resolved base fact profile and the reviewer's answers so far, run
the checklist and return the SINGLE highest-leverage material fact still unknown
(or signal the interview is complete). The MCP review flow loops this: each answer
is applied, the checklist re-runs, and dependent questions prune away — so the
reviewer is only asked the gating facts that actually matter, in priority order,
instead of a flat list.

  uv run python -m cli.next_question --base FC.profile.json \
      --questions FC.summary.json [--rules rules.json] [--answers answers.json]

Prints one JSON line: {"done": bool, "remaining": int, "question": {...}|null}.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.engine.checklist import Requirement, run_checklist

MATERIAL = {"statutory", "standard-material"}
FRONT_HALF = ("dividend_recommended", "average_employees_gt_250")


def _load_rules(rules_path: str | None, edition: str) -> list[Requirement]:
    if rules_path and Path(rules_path).exists():
        raw = json.loads(Path(rules_path).read_text(encoding="utf-8"))
        return [Requirement(r["id"], r["source"], r["reference"], r["edition"],
                            r["requirement_text"], r["trigger_type"],
                            r["trigger_condition"], tuple(r["trigger_facts"]),
                            r["direction"], r["severity"]) for r in raw]
    from db import store
    return store.get_active_requirements(edition)


def next_question(base: dict, answers: dict, pool: list[dict],
                  reqs: list[Requirement], edition: str) -> dict:
    profile = {**base, **answers}
    results = run_checklist(reqs, profile, edition)
    leverage: dict[str, int] = {}
    for r in results:
        req = r.requirement
        if (r.outcome == "undetermined" and req.direction in ("missing", "both")
                and req.severity in MATERIAL):
            for f in r.missing_facts:
                leverage[f] = leverage.get(f, 0) + 1
    known = set(profile)
    ranked = sorted((f for f in leverage if f not in known),
                    key=lambda f: (-leverage[f], f))
    # front-half statutory items: ask if still unanswered, after the checklist facts
    ranked += [f for f in FRONT_HALF if f not in known and f not in ranked]
    if not ranked:
        return {"done": True, "remaining": 0, "question": None}
    by_key = {q["fact_key"]: q for q in pool}
    top = ranked[0]
    q = by_key.get(top, {
        "fact_key": top, "topic": "", "why": "",
        "question": f"Please confirm: {top.replace('_', ' ')}?", "citation": ""})
    return {"done": False, "remaining": len(ranked), "question": q}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--questions", required=True, help="question pool (a summary "
                    "JSON with a 'questions' list, or a bare questions list)")
    ap.add_argument("--rules", help="cached active-rules JSON (else read the DB)")
    ap.add_argument("--answers", help="answers-so-far JSON (fact_key -> value)")
    ap.add_argument("--edition", default="pre-PR2024")
    args = ap.parse_args()

    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    pool_raw = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    pool = pool_raw["questions"] if isinstance(pool_raw, dict) else pool_raw
    answers = (json.loads(Path(args.answers).read_text(encoding="utf-8"))
               if args.answers else {})
    reqs = _load_rules(args.rules, args.edition)
    print(json.dumps(next_question(base, answers, pool, reqs, args.edition)))


if __name__ == "__main__":
    main()
