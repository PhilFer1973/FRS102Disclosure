"""Embed Tier 1 paragraph records with Voyage (voyage-3, 1024-dim).

Tier 1 = the requirements/citation corpus that backs RAG and citation
verification: FRS 102 (both editions), CA06 Part 15, SI 2008/410 Sch 1/5/7.
Embeddings are written to build/embeddings/ as a float32 .npy matrix plus a
parallel index JSONL — DB-independent, so the (paid) embedding step runs once
and any number of DB loads reuse it. input_type='document' (queries embed with
input_type='query' at retrieval time).

Model is voyage-3 to match db/migrations/0004 vector(1024). voyage-3-large is a
same-dimension quality upgrade needing no schema change — swap MODEL and re-run.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import voyageai
from dotenv import load_dotenv

from pipeline.records import read_jsonl

MODEL = "voyage-3"
DIM = 1024
TIER1 = ["build/frs102_2022.jsonl", "build/frs102_2024.jsonl",
         "build/ca06.jsonl", "build/si2008_410.jsonl"]
# USD per 1M tokens (Voyage published pricing, voyage-3 family), 2026-06.
PRICE_USD_PER_MTOK = 0.06

# Free-tier limits (no payment method): 3 RPM, 10K TPM. Stay safely under both:
# cap each request by estimated tokens and pause between requests. With a paid
# method the 200M free tokens still apply — set --fast to remove throttling.
FREE_MAX_TOKENS_PER_REQ = 3000   # ~ chars/4
FREE_MAX_TEXTS_PER_REQ = 32
FREE_SLEEP_S = 22.0              # ~2.7 req/min < 3 RPM
FAST_MAX_TEXTS_PER_REQ = 128
FAST_SLEEP_S = 0.0


def _batches(records, max_texts, max_tokens):
    batch, est = [], 0
    for r in records:
        rt = max(1, len(r.text) // 4)
        if batch and (len(batch) >= max_texts or est + rt > max_tokens):
            yield batch
            batch, est = [], 0
        batch.append(r)
        est += rt
    if batch:
        yield batch


_RETRYABLE = (voyageai.error.RateLimitError, voyageai.error.APIConnectionError,
              voyageai.error.ServiceUnavailableError, voyageai.error.Timeout)


def _embed_with_retry(client, texts, retries=8):
    for attempt in range(retries):
        try:
            return client.embed(texts, model=MODEL, input_type="document")
        except _RETRYABLE as e:
            wait = min(60 * (attempt + 1), 180)
            print(f"  {type(e).__name__}; backing off {wait}s "
                  f"(attempt {attempt + 1}/{retries})", flush=True)
            time.sleep(wait)
    raise SystemExit("repeated transient errors — aborting (progress is saved; re-run "
                     "to resume from the last checkpoint)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="build/embeddings")
    ap.add_argument("--fast", action="store_true",
                    help="no throttling (use only with a Voyage payment method)")
    args = ap.parse_args()

    load_dotenv()
    records = []
    for fn in TIER1:
        p = Path(fn)
        if not p.exists():
            raise SystemExit(f"missing Tier 1 source {fn} — run the parsers first")
        records.extend(read_jsonl(p))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    npy = out_dir / "tier1.npy"
    progress = out_dir / "tier1_progress.json"

    # Resume: reuse a partial matrix if it matches this corpus + model.
    done = 0
    if npy.exists() and progress.exists():
        pj = json.loads(progress.read_text())
        if pj.get("model") == MODEL and pj.get("count") == len(records):
            matrix = np.load(npy)
            done = pj.get("done", 0)
            print(f"resuming at {done}/{len(records)}", flush=True)
        else:
            matrix = np.zeros((len(records), DIM), dtype=np.float32)
    else:
        matrix = np.zeros((len(records), DIM), dtype=np.float32)

    max_texts = FAST_MAX_TEXTS_PER_REQ if args.fast else FREE_MAX_TEXTS_PER_REQ
    max_tokens = 10**9 if args.fast else FREE_MAX_TOKENS_PER_REQ
    sleep_s = FAST_SLEEP_S if args.fast else FREE_SLEEP_S
    print(f"embedding {len(records)} records with {MODEL} "
          f"({'fast' if args.fast else 'free-tier throttled'})", flush=True)

    client = voyageai.Client()
    total_tokens = 0
    pos = 0
    for batch in _batches(records, max_texts, max_tokens):
        if pos + len(batch) <= done:        # already embedded on a prior run
            pos += len(batch)
            continue
        result = _embed_with_retry(client, [r.text for r in batch])
        for i, emb in enumerate(result.embeddings):
            matrix[pos + i] = emb
        total_tokens += result.total_tokens
        pos += len(batch)
        np.save(npy, matrix)            # checkpoint after every request
        progress.write_text(json.dumps({"model": MODEL, "count": len(records),
                                        "done": pos}))
        print(f"  {pos}/{len(records)}", flush=True)
        if sleep_s and pos < len(records):
            time.sleep(sleep_s)

    with (out_dir / "tier1_index.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps({"source": r.source, "reference": r.reference,
                                 "edition": r.edition}, ensure_ascii=False) + "\n")
    meta = {"model": MODEL, "dim": DIM, "count": len(records),
            "tokens_this_run": total_tokens,
            "est_cost_usd_this_run": round(total_tokens * PRICE_USD_PER_MTOK / 1e6, 4)}
    (out_dir / "tier1_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"done: {matrix.shape} saved to {out_dir}; {total_tokens} tokens this run",
          flush=True)


if __name__ == "__main__":
    main()
