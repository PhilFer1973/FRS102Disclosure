"""Semantic retrieval over the paragraph store (RAG grounding for judgment).

Embeds a query with Voyage and returns the nearest FRS 102 paragraphs (edition-
filtered) by cosine distance — so judgment probes can ground their reasoning and
cite a real paragraph (CLAUDE.md: no citation, no finding).
"""

from __future__ import annotations

import os
import time

import psycopg
import voyageai
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

_RETRYABLE = (voyageai.error.RateLimitError, voyageai.error.APIConnectionError,
              voyageai.error.ServiceUnavailableError, voyageai.error.Timeout)


def _embed_query(query: str) -> list[float]:
    client = voyageai.Client()
    for attempt in range(6):
        try:
            return client.embed([query], model="voyage-3",
                                 input_type="query").embeddings[0]
        except _RETRYABLE:
            time.sleep(min(20 * (attempt + 1), 60))   # free-tier 3 RPM throttle
    raise SystemExit("Voyage embedding repeatedly rate-limited")


def retrieve(query: str, edition: str, k: int = 5,
             source: str = "FRS102") -> list[tuple[str, str]]:
    load_dotenv()
    qvec = _embed_query(query)
    with psycopg.connect(os.environ["SUPABASE_DB_URL"],
                         prepare_threshold=None) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                "select reference, text from paragraphs where source = %s "
                "and edition in ('both', %s) order by embedding <=> %s::vector "
                "limit %s", (source, edition, qvec, k))
            return cur.fetchall()
