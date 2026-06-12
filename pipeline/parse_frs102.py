"""Parse machine-extracted FRS 102 XML (page/block schema) into paragraph records.

The source files are first-pass PDF extractions: <body> -> <page> -> <block>,
with block types text-block, numbered-paragraph (@paragraph-id), section-heading
(@section) and appendix-heading (@appendix). Quirks handled here were verified
against the real files (Phase 0 structural report):

- Contents pages tag section rows as numbered-paragraph and appendix rows as
  appendix-heading; excluded via region tracking (no live section context).
- Page footers ("62\nFRS 102 (January 2022)") and footnotes are extracted as
  bare-number numbered-paragraphs; classified out, never silently dropped.
- Back matter (amendments lists, second glossary heading) quotes real paragraph
  ids (e.g. a duplicate 22.8 on a doc-appendix page); rejected because no
  section context is live there.
- Mislabelled section-headings exist (Companies Act "Section 394"/"Section 384"
  quoted in appendices); the section whitelist rejects them.
- Paragraph id families: section bodies hold ids like 4.2 / PBE34.1 / PBE34B.5;
  section appendices hold ids like 2A.4 (Appendix to Section 2), 1AC.3
  (Appendix C to Section 1A), 34A.6, 23A.12.
- A paragraph split across a page break can yield two blocks with the same id
  under the same live section; these are merged with a continuation log entry.
- More commonly, a page-split paragraph continues as a PLAIN text-block at the
  top of the next page (no paragraph-id). Detection: the paragraph is the last
  non-furniture block on its page, its text ends without terminal punctuation,
  and the next page's first non-furniture block is a text-block starting with
  a lowercase letter, digit or '('. Verified against the real files: 12 such
  splits in the 2022 edition, 14 in 2024 (e.g. 4.4A, 21.16, 23.41).
  Known limitation: a split paragraph followed by a footnote at the foot of the
  same page would not be detected (no such case found in either edition).
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.records import ParagraphRecord, normalize_text, write_jsonl

EDITION_MAP = {
    "January-2022": "pre-PR2024",
    "September-2024": "PR2024",
}

# Sections 1-35 plus lettered sections (1A small entities, 2A fair value in PR2024).
SECTION_RE = re.compile(r"^([1-9]|[12][0-9]|3[0-5])A?$")
DOC_APPENDICES = {"I", "II", "III", "IV"}
TO_SECTION_RE = re.compile(r"\bto Section (\d{1,2}A?)\b")


@dataclass
class Excluded:
    reason: str
    page: int
    detail: str
    snippet: str


@dataclass
class ParseResult:
    edition_raw: str
    edition: str
    records: list[ParagraphRecord]
    excluded: list[Excluded]  # numbered-paragraph blocks only
    merged_continuations: list[str]
    page_split_merges: list[str] = field(default_factory=list)
    heading_anomalies: list[Excluded] = field(default_factory=list)
    numbered_block_count: int = 0
    section_titles: dict[str, str] = field(default_factory=dict)

    def sequence_gaps(self) -> dict[str, list[int]]:
        """Missing integer steps per id family (e.g. 4.1..4.17 with no 4.9)."""
        family_ints: dict[str, set[int]] = {}
        for r in self.records:
            fam, _, num = r.reference.partition(".")
            m = re.match(r"^(\d+)", num)
            if m:
                family_ints.setdefault(fam, set()).add(int(m.group(1)))
        gaps: dict[str, list[int]] = {}
        for fam, ints in family_ints.items():
            missing = [n for n in range(1, max(ints)) if n not in ints]
            if missing:
                gaps[fam] = missing
        return gaps


def _family_ok(family: str, section: str) -> bool:
    """Is paragraph-id family valid inside `section` (body or its appendices)?"""
    for base in (section, "PBE" + section):
        if family == base:
            return True
        # one trailing appendix letter, e.g. 1AC under 1A, 2A under 2, PBE34B under 34
        if family.startswith(base) and len(family) == len(base) + 1 and family[-1].isalpha():
            return True
    return False


def _is_page_footer(pid: str, body_text: str) -> bool:
    rest = normalize_text(body_text)
    return bool(re.fullmatch(r"FRS 102( \([A-Za-z]+ \d{4}\))?", rest))


def _is_furniture(block: ET.Element) -> bool:
    """Headers/footers carrying no paragraph content."""
    btype = block.get("type", "")
    text = block.text or ""
    if btype == "numbered-paragraph":
        pid = block.get("paragraph-id", "")
        return "." not in pid and _is_page_footer(pid, text.removeprefix(pid))
    if btype == "text-block":
        t = normalize_text(text)
        return (not t or t.isdigit()
                or bool(re.match(r"^(Financial Reporting Council|FRS 102 \()", t)))
    return False


_ENDS_CLOSED_RE = re.compile(r"[.;:]['\")\]]?$")
_CONTINUATION_START_RE = re.compile(r"^[a-z(0-9]")


def _ends_open(text: str) -> bool:
    return not _ENDS_CLOSED_RE.search(text)


def parse_file(path: str | Path) -> ParseResult:
    root = ET.parse(path).getroot()
    edition_raw = root.get("edition", "")
    edition = EDITION_MAP.get(edition_raw)
    if edition is None:
        raise ValueError(f"unrecognised edition attribute: {edition_raw!r}")

    result = ParseResult(edition_raw=edition_raw, edition=edition, records=[],
                         excluded=[], merged_continuations=[])

    region = "front"  # front | section | section_appendix | doc_appendix
    current_section: str | None = None
    appendix_title: str | None = None
    by_ref: dict[str, ParagraphRecord] = {}

    body = root.find("body")
    if body is None:
        raise ValueError("no <body> element")

    carry: ParagraphRecord | None = None  # open paragraph from the previous page

    for page in body:
        page_no = int(page.get("number", "0"))
        blocks = list(page)
        nonfurn_idx = [i for i, b in enumerate(blocks) if not _is_furniture(b)]
        first_nf = nonfurn_idx[0] if nonfurn_idx else -1
        last_nf = nonfurn_idx[-1] if nonfurn_idx else -1
        page_tail: ParagraphRecord | None = None

        for i, block in enumerate(blocks):
            btype = block.get("type", "")
            text = block.text or ""

            if i == first_nf and carry is not None:
                merged = False
                if btype == "text-block":
                    cont = normalize_text(text)
                    if cont and _CONTINUATION_START_RE.match(cont):
                        carry.text = carry.text + " " + cont
                        result.page_split_merges.append(carry.reference)
                        if i == last_nf and _ends_open(cont):
                            page_tail = carry  # chain may continue on next page
                        merged = True
                carry = None
                if merged:
                    continue

            if btype == "section-heading":
                sec = block.get("section", "")
                lines = text.split("\n")
                if SECTION_RE.match(sec) and lines[0].strip() == f"Section {sec}":
                    region = "section"
                    current_section = sec
                    appendix_title = None
                    title = normalize_text(" ".join(lines[1:]))
                    if title:
                        result.section_titles[sec] = title
                else:
                    result.heading_anomalies.append(Excluded(
                        "non-frs-section-heading", page_no, sec, normalize_text(text)[:80]))

            elif btype == "appendix-heading":
                m = TO_SECTION_RE.search(text)
                if m and SECTION_RE.match(m.group(1)):
                    region = "section_appendix"
                    current_section = m.group(1)
                    appendix_title = normalize_text(text)
                elif region == "front":
                    pass  # contents-page row
                else:
                    region = "doc_appendix"
                    current_section = None
                    appendix_title = normalize_text(text)

            elif btype == "numbered-paragraph":
                result.numbered_block_count += 1
                pid = block.get("paragraph-id", "")
                body_text = normalize_text(text.removeprefix(pid))

                if "." not in pid:
                    if _is_page_footer(pid, text.removeprefix(pid)):
                        reason = "page-footer"
                    elif region == "front":
                        reason = "contents-row"
                    else:
                        reason = "footnote"
                    result.excluded.append(Excluded(reason, page_no, pid, body_text[:80]))
                    continue

                family = pid.partition(".")[0]
                in_live_section = (
                    region in ("section", "section_appendix") and current_section is not None
                )
                if not in_live_section or not _family_ok(family, current_section):
                    result.excluded.append(Excluded(
                        "outside-section-context", page_no, pid, body_text[:80]))
                    continue

                if pid in by_ref:
                    by_ref[pid].text += " " + body_text
                    result.merged_continuations.append(pid)
                    if i == last_nf and _ends_open(body_text):
                        page_tail = by_ref[pid]
                    continue

                section_label = f"Section {current_section}"
                title = result.section_titles.get(current_section)
                if title:
                    section_label += f" {title}"
                hierarchy = ["FRS 102", section_label]
                if region == "section_appendix" and appendix_title:
                    hierarchy.append(appendix_title)
                hierarchy.append(pid)

                record = ParagraphRecord(
                    source="FRS102",
                    reference=pid,
                    edition=edition,
                    text=body_text,
                    hierarchy=hierarchy,
                    location="section_body" if region == "section" else "section_appendix",
                    page=page_no,
                )
                by_ref[pid] = record
                result.records.append(record)
                if i == last_nf and _ends_open(body_text):
                    page_tail = record

        carry = page_tail

    return result


def reconciliation_report(result: ParseResult, source_name: str) -> str:
    lines = [
        f"# Reconciliation — {source_name} ({result.edition_raw})",
        "",
        f"Numbered-paragraph blocks in source: {result.numbered_block_count}",
        f"Accepted paragraph records:          {len(result.records)}",
        f"Merged same-id continuations:        {len(result.merged_continuations)}"
        + (f"  ({', '.join(result.merged_continuations)})" if result.merged_continuations else ""),
        f"Merged page-split text-blocks:       {len(result.page_split_merges)}"
        + (f"  ({', '.join(result.page_split_merges)})" if result.page_split_merges else ""),
        f"Excluded blocks:                     {len(result.excluded)}",
        "",
        "Accounting identity: accepted + merged + excluded "
        f"= {len(result.records) + len(result.merged_continuations) + len(result.excluded)} "
        f"(source blocks: {result.numbered_block_count})",
        "",
        "## Exclusions by reason",
    ]
    for reason, count in Counter(e.reason for e in result.excluded).most_common():
        lines.append(f"- {reason}: {count}")
    lines += ["", "## Records per section/family"]
    fam_counts = Counter(r.reference.partition(".")[0] for r in result.records)
    for fam in sorted(fam_counts, key=lambda f: (len(f), f)):
        lines.append(f"- {fam}: {fam_counts[fam]}")
    if result.heading_anomalies:
        lines += ["", "## Heading anomalies (mislabelled by extractor, ignored)"]
        for e in result.heading_anomalies:
            lines.append(f"- p{e.page} section={e.detail!r}: {e.snippet}")
    gaps = result.sequence_gaps()
    lines += [
        "",
        "## Integer sequence gaps per family",
        "Gaps are usually paragraphs deleted from the standard itself (e.g. 4.9-4.11)",
        "or by-design numbering (PBE34 starts at PBE34.64); cross-check via edition diff.",
    ]
    if gaps:
        for fam in sorted(gaps, key=lambda f: (len(f), f)):
            lines.append(f"- {fam}: missing {', '.join(map(str, gaps[fam]))}")
    else:
        lines.append("- none")
    lines += ["", "## Excluded blocks with section-like ids (audit trail)"]
    audit = [e for e in result.excluded if e.reason == "outside-section-context"]
    for e in audit:
        lines.append(f"- p{e.page} {e.detail}: {e.snippet}")
    if not audit:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("xml", help="FRS 102 source XML (frs102_2022.xml / frs102_2024.xml)")
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--report", help="write reconciliation report (markdown) here")
    args = ap.parse_args()

    result = parse_file(args.xml)
    write_jsonl(result.records, args.out)
    report = reconciliation_report(result, Path(args.xml).name)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    blocks = result.numbered_block_count
    accounted = len(result.records) + len(result.merged_continuations) + len(result.excluded)
    if blocks != accounted:
        raise SystemExit(f"RECONCILIATION FAILURE: {blocks} blocks vs {accounted} accounted")


if __name__ == "__main__":
    main()
