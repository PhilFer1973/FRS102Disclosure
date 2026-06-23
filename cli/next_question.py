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
import sys
from pathlib import Path

from pipeline.engine.checklist import Requirement, run_checklist
from pipeline.facts.builder import ALWAYS_ASK
from pipeline.fronthalf.review import front_half_questions

MATERIAL = {"statutory", "standard-material"}
FRONT_HALF = ("dividend_recommended", "average_employees_gt_250")

# The ONLY facts the interview may put to the reviewer: genuine judgements or
# external knowledge that cannot be read from the accounts. Everything else MUST
# be resolved from the accounts (computed, read, or defaulted) — never asked
# (Phil's standing rule). Inverting the default this way is what stops the
# "why are you asking me something that's in the accounts?" loop: a fact we
# haven't taught the resolver yet shows up as a logged GAP for us to fix, it does
# not get dumped on the reviewer.
ASKABLE = frozenset(ALWAYS_ASK | set(FRONT_HALF))


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
    # Only genuine reviewer-judgement facts may be asked. Anything else still
    # undetermined is a RESOLVER GAP — a fact that should have been read/computed
    # from the accounts — and is reported as a diagnostic, never as a question.
    askable = [f for f in ranked if f in ASKABLE]
    gaps = [f for f in ranked if f not in ASKABLE]
    if not askable:
        return {"done": True, "remaining": 0, "question": None, "resolver_gaps": gaps}
    ranked = askable
    # Pool lookup, augmented with the front-half question wording (those aren't in
    # the checklist question pool but can still be asked).
    by_key = {q.fact_key: {"fact_key": q.fact_key, "topic": q.topic,
                           "question": q.question_text, "why": q.why,
                           "citation": q.affected_refs[0] if q.affected_refs else ""}
              for q in front_half_questions()}
    by_key.update({q["fact_key"]: q for q in pool})
    top = ranked[0]
    src = by_key.get(top, {})
    # Normalise: the pool may carry 'affects' (a list) or 'citation' (a string).
    q = {
        "fact_key": top,
        "topic": src.get("topic", ""),
        "question": src.get("question", f"Please confirm: {top.replace('_', ' ')}?"),
        "why": src.get("why", ""),
        "citation": src.get("citation") or ", ".join(src.get("affects", []) or []),
    }
    return {"done": False, "remaining": len(ranked), "question": q,
            "resolver_gaps": gaps}


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
    result = next_question(base, answers, pool, reqs, args.edition)
    # Resolver gaps are a developer diagnostic (facts we should teach the resolver
    # to read/compute), NOT part of the reviewer-facing contract — log to stderr,
    # keep stdout's JSON line to {done, remaining, question}.
    gaps = result.pop("resolver_gaps", [])
    if gaps:
        print(f"[resolver gaps — undetermined material facts NOT asked (should be "
              f"read/computed from the accounts): {', '.join(gaps)}]", file=sys.stderr)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
