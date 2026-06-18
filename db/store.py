"""Persistence for engagements, runs and findings (Supabase Postgres).

Thin write layer used by the CLI runner. Connection via SUPABASE_DB_URL;
prepare_threshold=None for the Supabase pooler.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv

from pipeline.engine.checklist import Requirement
from pipeline.intake.router import Accepted
from pipeline.validate.checks import Finding


@contextmanager
def _connect():
    load_dotenv()
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        raise SystemExit("SUPABASE_DB_URL not set.")
    with psycopg.connect(dsn, autocommit=False, prepare_threshold=None) as conn:
        yield conn


def get_active_requirements(edition: str) -> list[Requirement]:
    """Active rules in scope for the engagement's edition (matching or 'both')."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, source, reference, edition, requirement_text, trigger_type, "
            "trigger_condition, trigger_facts, direction, severity from requirements "
            "where status = 'active' and edition in ('both', %s)", (edition,))
        return [Requirement(str(r[0]), r[1], r[2], r[3], r[4], r[5], r[6],
                            tuple(r[7] or ()), r[8], r[9]) for r in cur.fetchall()]


def get_fact_registry() -> dict[str, dict]:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("select key, description, value_type from fact_registry")
        return {r[0]: {"description": r[1], "value_type": r[2]}
                for r in cur.fetchall()}


def create_engagement(accepted: Accepted, materiality_basis: str | None = None,
                      materiality_value: float | None = None,
                      materiality_overridden: bool = False) -> str:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into engagements (entity_name, period_start, period_end, "
                "edition, materiality_basis, materiality_value, "
                "materiality_overridden) values (%s,%s,%s,%s,%s,%s,%s) returning id",
                (accepted.entity_name, accepted.period_start, accepted.period_end,
                 accepted.edition, materiality_basis, materiality_value,
                 materiality_overridden))
            eid = cur.fetchone()[0]
        conn.commit()
    return str(eid)


def create_run(engagement_id: str) -> tuple[str, int]:
    """Create the next sequential run for an engagement; returns (run_id, seq)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("select coalesce(max(sequence_no), 0) + 1 from runs "
                        "where engagement_id = %s", (engagement_id,))
            seq = cur.fetchone()[0]
            cur.execute(
                "insert into runs (engagement_id, sequence_no, status) "
                "values (%s, %s, 'in_progress') returning id",
                (engagement_id, seq))
            rid = cur.fetchone()[0]
        conn.commit()
    return str(rid), seq


def _identity_key(f: Finding) -> str:
    # findings dedupe across runs on (check_type, statement_location)
    return f"{f.check_type}|{f.location}"


_FORMATTING = {"note_numbering", "cross_reference_note"}


def _category(check_type: str) -> str:
    if check_type in _FORMATTING:
        return "formatting"
    if check_type == "judgment":
        return "judgment"
    return "numerical"


def write_findings(run_id: str, findings: list[Finding]) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "insert into findings (run_id, identity_key, category, direction, "
                "severity, citation, reasoning, source_loc, status) "
                "values (%s,%s,%s,NULL,%s,%s,%s,%s,'open')",
                [(run_id, _identity_key(f), _category(f.check_type), f.severity,
                  f.check_type, f.description, f.location) for f in findings])
        conn.commit()
    return len(findings)


def write_checklist_findings(run_id: str, results: list) -> int:
    """Write applicable required-disclosure results (trigger fired, missing
    direction) as checklist findings to verify against the accounts."""
    rows = []
    for res in results:
        req = res.requirement
        if res.outcome == "applicable" and req.direction in ("missing", "both"):
            rows.append((run_id, f"{req.id}|missing", "checklist", "missing",
                         req.severity, req.id, f"{req.source} {req.reference}",
                         "Required disclosure (trigger fired) — verify it is "
                         f"present: {req.requirement_text}"))
    if rows:
        with _connect() as conn, conn.cursor() as cur:
            cur.executemany(
                "insert into findings (run_id, identity_key, category, direction, "
                "severity, requirement_id, citation, reasoning, status) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,'open')", rows)
            conn.commit()
    return len(rows)


def write_presence_findings(run_id: str, presence_results: list) -> int:
    """Write disclosure findings from presence detection: absent => missing
    disclosure; unclear => verify; present => satisfied (no finding)."""
    rows = []
    for p in presence_results:
        req = p.requirement.requirement
        if p.status == "absent":
            reasoning = f"MISSING required disclosure: {req.requirement_text}"
        elif p.status == "unclear":
            reasoning = ("Could not confirm this required disclosure is present "
                         f"— verify: {req.requirement_text}")
        else:
            continue
        rows.append((run_id, f"{req.id}|missing", "checklist", "missing",
                     req.severity, req.id, f"{req.source} {req.reference}",
                     reasoning))
    if rows:
        with _connect() as conn, conn.cursor() as cur:
            cur.executemany(
                "insert into findings (run_id, identity_key, category, direction, "
                "severity, requirement_id, citation, reasoning, status) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,'open')", rows)
            conn.commit()
    return len(rows)


def get_prior_run(engagement_id: str, before_seq: int) -> str | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("select id from runs where engagement_id = %s and sequence_no < %s "
                    "order by sequence_no desc limit 1", (engagement_id, before_seq))
        row = cur.fetchone()
        return str(row[0]) if row else None


def get_run_findings(run_id: str) -> list[dict]:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("select identity_key, category, severity, citation, reasoning, "
                    "status, disposition from findings where run_id = %s", (run_id,))
        cols = ("identity_key", "category", "severity", "citation", "reasoning",
                "status", "disposition")
        return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]


def resolved_keys_for_engagement(engagement_id: str) -> set[str]:
    """Identity keys ever dispositioned resolved/accepted on this engagement —
    a re-appearance of one is a regression, not a new finding."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "select distinct f.identity_key from findings f join runs r "
            "on r.id = f.run_id where r.engagement_id = %s and "
            "(f.status = 'resolved' or f.disposition in ('accept','resolved'))",
            (engagement_id,))
        return {r[0] for r in cur.fetchall()}


def write_questions(run_id: str, round_no: int, questions: list) -> int:
    if not questions:
        return 0
    with _connect() as conn, conn.cursor() as cur:
        cur.executemany(
            "insert into questions (run_id, round, fact_key, question_text, "
            "provenance) values (%s,%s,%s,%s,%s)",
            [(run_id, round_no, q.fact_key, q.question_text, q.provenance)
             for q in questions])
        conn.commit()
    return len(questions)


def complete_run(run_id: str, status: str = "complete",
                 assumptions: list[str] | None = None) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update runs set status = %s, assumptions = %s, "
                "completed_at = now() where id = %s",
                (status, assumptions or [], run_id))
        conn.commit()
