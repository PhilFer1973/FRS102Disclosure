"""Align FRS 102 2022 vs 2024 paragraph records and classify changes.

Paragraphs are aligned by reference (paragraph id). Classification:
- unchanged: normalised text identical
- amended:   present in both editions, text differs (similarity ratio recorded;
             low ratios = substantive rewrites, ~0.99 may be extraction noise —
             the ratio is kept so a human can judge)
- new:       only in the September 2024 (PR2024) edition
- deleted:   only in the January 2022 (pre-PR2024) edition

Edition applicability for the requirements pipeline:
unchanged -> 'both'; amended -> one row per edition; new -> 'PR2024';
deleted -> 'pre-PR2024'.

Grouping is by paragraph-id family (section or appendix prefix: 4, 1AC, 2A,
PBE34...). Note 2A compares the 2022 Appendix to Section 2 (fair value) with
the 2024 Section 2A — a genuine like-for-like comparison, since the Periodic
Review promoted that appendix to a full section.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pipeline.records import ParagraphRecord, read_jsonl


@dataclass
class DiffEntry:
    reference: str
    family: str
    status: str  # unchanged | amended | new | deleted
    similarity: float | None  # only for amended
    applicability: str  # both | pre-PR2024 | PR2024

    def row(self) -> dict:
        return self.__dict__


def _family(reference: str) -> str:
    return reference.partition(".")[0]


def diff_records(old: list[ParagraphRecord], new: list[ParagraphRecord]) -> list[DiffEntry]:
    a = {r.reference: r for r in old}
    b = {r.reference: r for r in new}
    entries: list[DiffEntry] = []
    for ref in sorted(a.keys() | b.keys(), key=lambda x: (len(_family(x)), x)):
        fam = _family(ref)
        if ref in a and ref in b:
            if a[ref].text == b[ref].text:
                entries.append(DiffEntry(ref, fam, "unchanged", None, "both"))
            else:
                ratio = SequenceMatcher(None, a[ref].text, b[ref].text).ratio()
                entries.append(DiffEntry(ref, fam, "amended", round(ratio, 4), "both"))
        elif ref in a:
            entries.append(DiffEntry(ref, fam, "deleted", None, "pre-PR2024"))
        else:
            entries.append(DiffEntry(ref, fam, "new", None, "PR2024"))
    return entries


def section_summary(entries: list[DiffEntry]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {"unchanged": 0, "amended": 0, "new": 0, "deleted": 0})
    for e in entries:
        summary[e.family][e.status] += 1
    return dict(summary)


def _change_pct(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    changed = counts["amended"] + counts["new"] + counts["deleted"]
    return 100.0 * changed / total if total else 0.0


def report_markdown(entries: list[DiffEntry]) -> str:
    summary = section_summary(entries)
    overall = {"unchanged": 0, "amended": 0, "new": 0, "deleted": 0}
    for counts in summary.values():
        for k in overall:
            overall[k] += counts[k]

    lines = [
        "# FRS 102 edition diff — January 2022 vs September 2024 (Periodic Review)",
        "",
        f"Total aligned references: {sum(overall.values())} "
        f"(unchanged {overall['unchanged']}, amended {overall['amended']}, "
        f"new {overall['new']}, deleted {overall['deleted']})",
        "",
        "Similarity is shown for amended paragraphs in the JSONL output; ratios near",
        "1.0 may be PDF-extraction noise rather than substantive amendment.",
        "",
        "| Family | Unchanged | Amended | New | Deleted | Total | % changed |",
        "|---|---|---|---|---|---|---|",
    ]
    for fam in sorted(summary, key=lambda f: (len(f.lstrip("PBE") or f), f)):
        c = summary[fam]
        total = sum(c.values())
        lines.append(
            f"| {fam} | {c['unchanged']} | {c['amended']} | {c['new']} | "
            f"{c['deleted']} | {total} | {_change_pct(c):.0f}% |")

    lines += ["", "## Periodic Review sanity check", ""]
    for fam, label in (("23", "Section 23 Revenue (rewritten)"),
                       ("20", "Section 20 Leases (substantially amended)")):
        pct = _change_pct(summary.get(fam, {"unchanged": 0, "amended": 0, "new": 0, "deleted": 0}))
        verdict = "OK" if pct >= 50 else "**UNEXPECTED — investigate**"
        lines.append(f"- {label}: {pct:.0f}% changed — {verdict}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("old_jsonl", help="parsed pre-PR2024 records (frs102_2022.jsonl)")
    ap.add_argument("new_jsonl", help="parsed PR2024 records (frs102_2024.jsonl)")
    ap.add_argument("--out", required=True, help="diff entries JSONL")
    ap.add_argument("--report", required=True, help="markdown summary report")
    args = ap.parse_args()

    entries = diff_records(read_jsonl(args.old_jsonl), read_jsonl(args.new_jsonl))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e.row(), ensure_ascii=False) + "\n")
    report = report_markdown(entries)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
