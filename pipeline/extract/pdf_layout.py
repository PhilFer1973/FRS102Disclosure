"""Azure Document Intelligence 'prebuilt-layout' client for PDF extraction.

The Layout model returns text, tables (cells with row/column spans), selection
marks and paragraph roles, each with bounding regions (page + polygon) — the raw
material the FS-model builder turns into typed statement tables with source
coordinates. This module is the thin client; the model->FS mapping is built next,
against real Layout output from a sample set of accounts.

Credentials from .env: AZURE_DOCINTEL_ENDPOINT, AZURE_DOCINTEL_KEY.
Pricing: Layout is ~$0.01/page on the S0 tier.

NOTE: untested until first run against the live service (needs the resource +
a sample PDF). The SDK surface is pinned via azure-ai-documentintelligence>=1.0.2.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _client():
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    load_dotenv()
    endpoint = os.environ.get("AZURE_DOCINTEL_ENDPOINT")
    key = os.environ.get("AZURE_DOCINTEL_KEY")
    if not endpoint or not key:
        raise SystemExit(
            "AZURE_DOCINTEL_ENDPOINT / AZURE_DOCINTEL_KEY not set. Provision an "
            "Azure Document Intelligence resource (UK South, S0) and add both to .env.")
    return DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))


def analyze_pdf(path: str | Path) -> Any:
    """Run prebuilt-layout over a PDF; returns the AnalyzeResult."""
    data = Path(path).read_bytes()
    poller = _client().begin_analyze_document(
        "prebuilt-layout", body=data, content_type="application/pdf")
    return poller.result()


def layout_summary(result: Any) -> dict:
    """Compact summary for sanity-checking an extraction (no PII assumptions)."""
    pages = getattr(result, "pages", []) or []
    tables = getattr(result, "tables", []) or []
    return {
        "pages": len(pages),
        "tables": len(tables),
        "table_shapes": [(t.row_count, t.column_count) for t in tables[:20]],
        "words": sum(len(getattr(p, "words", []) or []) for p in pages),
        "first_page_lines": [ln.content for p in pages[:1]
                             for ln in (getattr(p, "lines", []) or [])[:15]],
    }
