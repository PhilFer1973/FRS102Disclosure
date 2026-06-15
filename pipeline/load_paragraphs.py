"""Load Tier 1 paragraph records into the Supabase `paragraphs` table.

Combines: parsed Tier 1 records (FRS 102 both editions + CA06 Part 15 +
SI Sch 1/5/7), para_type classifications (FRS only; legislation stays null),
and Voyage embeddings (build/embeddings/tier1.npy + index). Upserts by the
table's (source, reference, edition) unique key, so re-running is safe.

Needs SUPABASE_DB_URL and the migrations already applied (see db.apply_migrations).
Run pipeline.embed_corpus first so embeddings exist; --no-embeddings loads text
only (embedding column left NULL) if you want to defer the vector load.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

from pipeline.records import read_jsonl

TIER1 = ["build/frs102_2022.jsonl", "build/frs102_2024.jsonl",
         "build/ca06.jsonl", "build/si2008_410.jsonl"]


def load_para_types() -> dict[tuple[str, str], str]:
    path = Path("build/para_types.jsonl")
    out: dict[tuple[str, str], str] = {}
    if path.exists():
        for line in path.open(encoding="utf-8"):
            if line.strip():
                row = json.loads(line)
                if row.get("para_type"):
                    out[(row["edition"], row["reference"])] = row["para_type"]
    return out


def load_embeddings(out_dir: Path) -> dict[tuple[str, str, str], np.ndarray]:
    npy, idx = out_dir / "tier1.npy", out_dir / "tier1_index.jsonl"
    progress = out_dir / "tier1_progress.json"
    if not (npy.exists() and idx.exists()):
        raise SystemExit("no embeddings found — run pipeline.embed_corpus "
                         "or pass --no-embeddings")
    if progress.exists():
        pj = json.loads(progress.read_text())
        if pj.get("done", 0) < pj.get("count", 1):
            raise SystemExit(f"embeddings incomplete ({pj['done']}/{pj['count']}); "
                             "wait for embed_corpus to finish or pass --no-embeddings")
    matrix = np.load(npy)
    keys = [json.loads(line) for line in idx.open(encoding="utf-8") if line.strip()]
    return {(k["source"], k["reference"], k["edition"]): matrix[i]
            for i, k in enumerate(keys)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-embeddings", action="store_true")
    ap.add_argument("--embeddings-dir", default="build/embeddings")
    args = ap.parse_args()

    load_dotenv()
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        raise SystemExit("SUPABASE_DB_URL not set (see db.apply_migrations).")

    records = []
    for fn in TIER1:
        records.extend(read_jsonl(fn))
    para_types = load_para_types()
    embeddings = ({} if args.no_embeddings
                  else load_embeddings(Path(args.embeddings_dir)))

    rows = []
    for r in records:
        pt = para_types.get((r.edition, r.reference))
        emb = embeddings.get((r.source, r.reference, r.edition))
        rows.append((r.source, r.reference, r.edition, pt, r.text,
                     r.hierarchy, None if emb is None else np.asarray(emb)))

    print(f"loading {len(rows)} paragraph rows "
          f"({'with' if not args.no_embeddings else 'without'} embeddings)", flush=True)

    with psycopg.connect(dsn, autocommit=False) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(
                "insert into paragraphs "
                "(source, reference, edition, para_type, text, hierarchy, embedding) "
                "values (%s, %s, %s, %s, %s, %s, %s) "
                "on conflict (source, reference, edition) do update set "
                "para_type = excluded.para_type, text = excluded.text, "
                "hierarchy = excluded.hierarchy, embedding = excluded.embedding",
                rows)
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("select source, count(*) from paragraphs group by source "
                        "order by source")
            counts = cur.fetchall()
    print("loaded. paragraphs by source:", dict(counts))


if __name__ == "__main__":
    main()
