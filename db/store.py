"""Persistence for engagements, runs and findings (Supabase Postgres).

Thin write layer used by the CLI runner. Connection via SUPABASE_DB_URL;
prepare_threshold=None for the Supabase pooler.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv

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
    # numerical findings dedupe across runs on (check_type, statement_location)
    return f"{f.check_type}|{f.location}"


def write_findings(run_id: str, findings: list[Finding]) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "insert into findings (run_id, identity_key, category, direction, "
                "severity, citation, reasoning, source_loc, status) "
                "values (%s,%s,'numerical',NULL,%s,%s,%s,%s,'open')",
                [(run_id, _identity_key(f), f.severity, f.check_type,
                  f.description, f.location) for f in findings])
        conn.commit()
    return len(findings)


def complete_run(run_id: str, status: str = "complete",
                 assumptions: list[str] | None = None) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update runs set status = %s, assumptions = %s, "
                "completed_at = now() where id = %s",
                (status, assumptions or [], run_id))
        conn.commit()
