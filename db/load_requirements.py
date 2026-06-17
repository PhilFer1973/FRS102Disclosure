"""Promote v2 draft checklist rows into the requirements table (V1).

Owner-authorised "best assessment" promotion (2026-06): rather than a full human
sign-off of all 584 rows, a transparent triage activates the safe, high-value
core and holds the dangerous minority for later review.

  - status 'active'     : missing-direction, non-statutory rows (core promise;
                          over-flag is the safe failure mode, caught at the
                          per-engagement review).
  - status 'in_review'  : every statutory row (materiality-blind) and every
                          untriggered/both row (the asymmetric "confirm
                          immaterial" downside). Dormant until human sign-off.
  - status 'rejected'   : rows the auto-amend pass found unsupported (dropped).

Also: applies the fact-key merge proposals, registers the fact vocabulary
(inferred value_type — placeholders for human refinement), and stamps every row
with its provenance. This is Claude's QA assessment, NOT an ICAEW sign-off.

Full reload: clears requirements first (sole loader). Re-run safe.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROWS_DIR = Path("build/rows_v2")
MERGES = Path("build/key_merge_proposals.json")
CHALLENGE = Path("build/challenge_results.jsonl")

_BOOL_PREFIX = ("has_", "is_", "applies_", "presents_", "uses_", "elected_",
                "had_", "requires_", "provides_", "discloses_", "holds_",
                "incurred_", "made_", "recognises_", "operates_")
_NUM_SUFFIX = ("_amount", "_value", "_total", "_number", "_count", "_rate",
               "_percentage")


def infer_value_type(key: str) -> str:
    if key.endswith("_date"):
        return "date"
    if key.endswith(_NUM_SUFFIX) or "number_of_" in key:
        return "number"
    if key.startswith(_BOOL_PREFIX) or key.endswith(("_required", "_present")):
        return "boolean"
    return "text"


def build_merge_map(merge_groups: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for g in merge_groups:
        for m in g["members"]:
            if m != g["canonical"]:
                out[m] = g["canonical"]
    return out


def apply_merges(row: dict, merge_map: dict[str, str]) -> dict:
    facts = [merge_map.get(f, f) for f in row.get("trigger_facts", [])]
    # dedupe preserving order
    row = {**row, "trigger_facts": list(dict.fromkeys(facts))}
    cond = row.get("trigger_condition")
    if cond:
        for member, canonical in sorted(merge_map.items(), key=lambda kv: -len(kv[0])):
            cond = re.sub(rf"\b{re.escape(member)}\b", canonical, cond)
        row["trigger_condition"] = cond
    return row


def triage_status(row: dict) -> str:
    if row["severity"] == "statutory" or row["direction"] in ("untriggered", "both"):
        return "in_review"
    return "active"


def _normalise(row: dict, status: str, stamp: str) -> dict:
    tt, cond = row["trigger_type"], row.get("trigger_condition")
    # CHECK: conditional rows must carry a condition. Synthesize from a single
    # fact, else placeholder + hold for review (never activate a malformed one).
    if tt == "conditional" and not (cond and cond.strip()):
        facts = row.get("trigger_facts", [])
        if len(facts) == 1:
            cond = f"{facts[0]} == true"
        else:
            cond = "[condition missing — review]"
            status = "in_review"
    grade = row.get("_grade", "?")
    note = (f"[auto-promoted {stamp}; status={status}; challenge={grade}; "
            f"amended={row.get('amended', False)}] {row.get('review_notes', '')}").strip()
    return {**row, "trigger_condition": cond, "status": status, "review_notes": note}


def build_rows() -> tuple[list[dict], set[str]]:
    merge_map = build_merge_map(json.loads(MERGES.read_text())["groups"]) \
        if MERGES.exists() else {}
    grades = {}
    if CHALLENGE.exists():
        for line in CHALLENGE.open(encoding="utf-8"):
            if line.strip():
                c = json.loads(line)
                grades[c["row_id"]] = c.get("grade", "?")
    stamp = date.today().isoformat()

    out: list[dict] = []
    keys: set[str] = set()
    # active/in_review rows
    for path in sorted(ROWS_DIR.glob("section_*_rows.jsonl")):
        for line in path.open(encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_grade"] = grades.get(re.sub(r"-s\d+$", "", row.get("_row_id", "")), "?")
            row = apply_merges(row, merge_map)
            row = _normalise(row, triage_status(row), stamp)
            keys.update(row["trigger_facts"])
            out.append(row)
    # dropped rows -> rejected (audit trail)
    dropped = ROWS_DIR / "dropped.jsonl"
    if dropped.exists():
        for line in dropped.open(encoding="utf-8"):
            if line.strip():
                row = apply_merges(json.loads(line), merge_map)
                row = _normalise(row, "rejected", stamp)
                keys.update(row["trigger_facts"])
                out.append(row)
    return out, keys


def main() -> None:
    load_dotenv()
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        raise SystemExit("SUPABASE_DB_URL not set.")
    rows, keys = build_rows()

    with psycopg.connect(dsn, autocommit=False, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            cur.execute("delete from requirements")  # full reload (sole loader)
            cur.executemany(
                "insert into fact_registry (key, description, value_type) "
                "values (%s,%s,%s) on conflict (key) do update set "
                "value_type = excluded.value_type",
                [(k, f"{k.replace('_', ' ')} (auto; review)", infer_value_type(k))
                 for k in sorted(keys)])
            cur.executemany(
                "insert into requirements (source, reference, edition, applies_to, "
                "requirement_text, trigger_type, trigger_condition, trigger_facts, "
                "direction, severity, review_notes, status) "
                "values (%s,%s,%s,'all',%s,%s,%s,%s,%s,%s,%s,%s)",
                [(r["source"], r["reference"], r["edition"], r["requirement_text"],
                  r["trigger_type"], r["trigger_condition"], r["trigger_facts"],
                  r["direction"], r["severity"], r["review_notes"], r["status"])
                 for r in rows])
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("select status, count(*) from requirements group by status "
                        "order by status")
            by_status = dict(cur.fetchall())
            cur.execute("select count(*) from fact_registry")
            n_facts = cur.fetchone()[0]
    print(f"loaded {len(rows)} requirements: {by_status}")
    print(f"fact_registry: {n_facts} keys")


if __name__ == "__main__":
    main()
