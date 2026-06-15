"""Apply db/migrations/*.sql to Supabase Postgres, in order, once each.

Connects via SUPABASE_DB_URL (the Postgres connection string / URI — NOT the
REST service key, which cannot run DDL). Tracks applied files in a
schema_migrations table; each file runs in its own transaction. Re-running is
safe: already-applied files are skipped.

  SUPABASE_DB_URL=postgresql://postgres:<pwd>@<host>:5432/postgres

Usage:
  uv run python -m db.apply_migrations --dry-run   # list pending, connect-test
  uv run python -m db.apply_migrations             # apply pending
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

MIGRATIONS_DIR = Path("db/migrations")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        raise SystemExit(
            "SUPABASE_DB_URL not set. Add the Supabase Postgres connection string "
            "(Project Settings -> Database -> Connection string -> URI) to .env.")

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        raise SystemExit(f"no .sql files in {MIGRATIONS_DIR}")

    with psycopg.connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("create table if not exists schema_migrations ("
                        "filename text primary key, applied_at timestamptz default now())")
            conn.commit()
            cur.execute("select filename from schema_migrations")
            applied = {r[0] for r in cur.fetchall()}

        pending = [f for f in files if f.name not in applied]
        print(f"connected. {len(applied)} applied, {len(pending)} pending.")
        for f in pending:
            print(f"  pending: {f.name}")
        if args.dry_run:
            print("dry run — nothing applied.")
            return

        for f in pending:
            sql = f.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute("insert into schema_migrations (filename) values (%s)",
                                (f.name,))
                conn.commit()
                print(f"applied {f.name}")
            except Exception as e:
                conn.rollback()
                raise SystemExit(f"FAILED on {f.name}: {e}\n"
                                 "Transaction rolled back; fix and re-run.") from e
        print("all migrations applied.")


if __name__ == "__main__":
    main()
