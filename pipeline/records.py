"""Shared paragraph record type and JSONL persistence."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

SOURCES = ("FRS102", "CA06", "SI2008/410")
EDITIONS = ("pre-PR2024", "PR2024", "both")


@dataclass
class ParagraphRecord:
    source: str  # one of SOURCES
    reference: str  # e.g. '4.2', '1AC.3', 'PBE34.1', 's411(1A)', 'Sch1 para 45(2)'
    edition: str  # one of EDITIONS
    text: str
    hierarchy: list[str] = field(default_factory=list)
    location: str = ""  # 'section_body' | 'section_appendix' | 'provision' | 'schedule'
    page: int | None = None  # FRS sources only (PDF page of extraction)

    def __post_init__(self) -> None:
        if self.source not in SOURCES:
            raise ValueError(f"unknown source: {self.source!r}")
        if self.edition not in EDITIONS:
            raise ValueError(f"unknown edition: {self.edition!r}")
        if not self.reference:
            raise ValueError("reference must be non-empty")


def normalize_text(raw: str) -> str:
    """Normalise extraction artefacts: ligatures (NFKC), soft hyphens, whitespace."""
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("­", "")
    return " ".join(text.split())


def write_jsonl(records: list[ParagraphRecord], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[ParagraphRecord]:
    out: list[ParagraphRecord] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(ParagraphRecord(**json.loads(line)))
    return out
