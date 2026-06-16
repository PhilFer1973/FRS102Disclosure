"""Parse legislation.gov.uk CLML XML (CA06, SI 2008/410) into paragraph records.

Structure (verified against the real files, Phase 0 structural report):
Legislation -> Primary|Secondary -> Body (Part -> Chapter -> Pblock -> P1group -> P1)
and -> Schedules (Schedule -> ... -> P1). Sections/regulations/schedule paragraphs
are P1 (id="section-411" / "regulation-4" / "schedule-1-...paragraph-45");
subsections are P2. Printed numbers come from <Pnumber> (read via itertext so
Addition/Substitution wrappers are transparent); the consolidated text is read
as-is and commentary apparatus (CommentaryRef) contributes no text.

Record granularity: one record per P2 (subsection); a P1 with no P2 children
yields a single P1-level record; direct Text under P1para alongside P2s yields
a P1-level intro record. P3+ nested content is included in its P2's text.

Default scope filters (per locked project scope):
- CA06: Part 15 only (--part to override)
- SI 2008/410: all regulations + Schedules 1, 5, 7 (--schedules to override)
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.records import ParagraphRecord, normalize_text, write_jsonl

NS = "{http://www.legislation.gov.uk/namespaces/legislation}"
UKM = "{http://www.legislation.gov.uk/namespaces/metadata}"
DC = "{http://purl.org/dc/elements/1.1/}"

SOURCE_BY_URI = {
    "/ukpga/2006/46": "CA06",
    "/uksi/2008/410": "SI2008/410",
}


@dataclass
class LegParseResult:
    source: str
    title: str
    declared_provisions: int
    p1_seen: int = 0
    p1_nested: int = 0  # P1s inside BlockAmendment quoted text; text captured via parent
    p1_in_scope: int = 0
    records: list[ParagraphRecord] = field(default_factory=list)
    skipped_out_of_scope: dict[str, int] = field(default_factory=dict)
    reference_fallbacks: list[str] = field(default_factory=list)
    # Same reference emitted twice = amendment versions coexisting in the
    # consolidated snapshot. The in-force (amended) variant is kept; the
    # superseded variant is recorded here. See _prefer_variant.
    ref_index: dict[str, int] = field(default_factory=dict)
    duplicate_references: list[tuple[str, str]] = field(default_factory=list)


def _itext(el: ET.Element | None) -> str:
    return normalize_text("".join(el.itertext())) if el is not None else ""


def _prose(el: ET.Element | None) -> str:
    """Text assembly for record bodies: like itertext, but renders nested Pnumber
    elements with their print punctuation (default parentheses), so P3 list items
    read '(a) which qualifies...' not 'awhich qualifies...'."""
    if el is None:
        return ""
    parts: list[str] = []

    def rec(e: ET.Element) -> None:
        if e.tag == NS + "Pnumber":
            pb = e.get("PuncBefore", "(")
            pa = e.get("PuncAfter", ")")
            parts.append(f" {pb}{''.join(e.itertext())}{pa} ")
            return
        if e.text:
            parts.append(e.text)
        for c in e:
            rec(c)
            if c.tail:
                parts.append(c.tail)

    rec(el)
    return normalize_text("".join(parts))


def _child(el: ET.Element, tag: str) -> ET.Element | None:
    return el.find(NS + tag)


def _pnumber(el: ET.Element) -> str:
    return _itext(_child(el, "Pnumber"))


def _heading(el: ET.Element) -> str:
    """'Part 15 Accounts and reports' style label from Number + Title children."""
    number = _itext(_child(el, "Number"))
    title = _itext(_child(el, "Title"))
    return " — ".join(x for x in (number, title) if x)


def _schedule_number(sched: ET.Element) -> str:
    num = _itext(_child(sched, "Number"))
    m = re.search(r"SCHEDULE\s+(\w+)", num, re.IGNORECASE)
    return m.group(1) if m else num or "?"


def _p1_reference(p1: ET.Element, source: str, sched_no: str | None,
                  result: LegParseResult) -> str:
    num = _pnumber(p1)
    if not num:
        pid = p1.get("id", "")
        m = re.search(r"paragraph-([\w]+)$", pid) or re.search(r"-(\w+)$", pid)
        num = m.group(1) if m else pid
        result.reference_fallbacks.append(pid)
    if sched_no is not None:
        return f"Sch {sched_no} para {num}"
    return f"reg {num}" if source == "SI2008/410" else f"s{num}"


def _prefer_variant(new_text: str, existing_text: str) -> bool:
    """For amendment-version duplicates, is `new_text` the in-force variant to
    keep over `existing_text`? Verified against legislation.gov.uk (corroborated
    2026-06): the Economic Crime and Corporate Transparency Act 2023 amended
    CA06 s445(7)/s446(5) to cite s443A (micro-entities); keep the 443A-citing
    (amended) variant over the superseded 444-only one. Otherwise keep the
    first seen (document order)."""
    return "443A" in new_text and "443A" not in existing_text


def _emit(result: LegParseResult, reference: str, text: str,
          hierarchy: list[str], location: str) -> None:
    if not text:
        text = "[no text — repealed or empty provision]"
    record = ParagraphRecord(source=result.source, reference=reference,
                             edition="both", text=text, hierarchy=hierarchy,
                             location=location)
    if reference in result.ref_index:
        i = result.ref_index[reference]
        existing = result.records[i]
        if _prefer_variant(text, existing.text):
            result.records[i] = record
            result.duplicate_references.append(
                (reference, f"REPLACED superseded variant: {existing.text[:80]}"))
        else:
            result.duplicate_references.append(
                (reference, f"dropped alternate variant: {text[:80]}"))
        return
    result.ref_index[reference] = len(result.records)
    result.records.append(record)


def _parse_p1(p1: ET.Element, ctx: list[str], result: LegParseResult,
              sched_no: str | None) -> None:
    result.p1_in_scope += 1
    result.p1_nested += sum(1 for el in p1.iter(NS + "P1")) - 1
    ref = _p1_reference(p1, result.source, sched_no, result)
    location = "schedule" if sched_no is not None else "provision"
    hierarchy = [*ctx, ref]

    p1para = _child(p1, "P1para")
    if p1para is None:
        _emit(result, ref, _prose(p1).removeprefix(_pnumber(p1)).strip(), hierarchy, location)
        return

    p2s = p1para.findall(NS + "P2")
    intro_texts = [_prose(t) for t in p1para.findall(NS + "Text")]
    intro = " ".join(t for t in intro_texts if t)

    if not p2s:
        _emit(result, ref, _prose(p1para), hierarchy, location)
        return
    if intro:
        _emit(result, ref, intro, hierarchy, location)
    for p2 in p2s:
        sub = _pnumber(p2)
        sub_ref = f"{ref}({sub})" if sub else ref
        p2para = _child(p2, "P2para")
        _emit(result, sub_ref, _prose(p2para if p2para is not None else p2),
              [*hierarchy, f"({sub})"], location)


def _walk(el: ET.Element, ctx: list[str], result: LegParseResult,
          in_scope: bool, sched_no: str | None, scope_label: str) -> None:
    for child in el:
        tag = child.tag.removeprefix(NS)
        if tag == "P1":
            result.p1_seen += 1
            if in_scope:
                _parse_p1(child, ctx, result, sched_no)
            else:
                result.p1_nested += sum(1 for el in child.iter(NS + "P1")) - 1
                result.skipped_out_of_scope[scope_label] = (
                    result.skipped_out_of_scope.get(scope_label, 0) + 1)
        elif tag in ("Part", "Chapter", "Pblock", "P1group"):
            label = _heading(child) if tag != "P1group" else _itext(_child(child, "Title"))
            new_ctx = [*ctx, label] if label else ctx
            _walk(child, new_ctx, result, in_scope, sched_no, scope_label)
        else:
            _walk(child, ctx, result, in_scope, sched_no, scope_label)


def parse_file(path: str | Path, part: str | None = None,
               schedules: set[str] | None = None) -> LegParseResult:
    """part: keep only this Body Part number (e.g. '15'); None = all.
    schedules: keep only these schedule numbers (e.g. {'1','5','7'}); None = all."""
    root = ET.parse(path).getroot()
    uri = root.get("IdURI", "") + root.get("DocumentURI", "")
    source = next((s for frag, s in SOURCE_BY_URI.items() if frag in uri), None)
    if source is None:
        raise ValueError(f"unrecognised legislation document: {uri!r}")
    title = ""
    for el in root.iter(DC + "title"):
        title = normalize_text(el.text or "")
        break
    declared = int(root.get("NumberOfProvisions", "0"))
    result = LegParseResult(source=source, title=title, declared_provisions=declared)

    doc = root.find(NS + "Primary")
    if doc is None:
        doc = root.find(NS + "Secondary")
    if doc is None:
        raise ValueError("no Primary/Secondary element found")

    body = doc.find(NS + "Body")
    if body is not None:
        for part_el in body.findall(NS + "Part"):
            label = _heading(part_el)
            num = _itext(_child(part_el, "Number"))
            keep = part is None or re.fullmatch(rf"Part\s+{re.escape(part)}", num or "")
            _walk(part_el, [title, label], result, bool(keep), None,
                  label or "unnumbered part")
        # P1s directly under Body, outside any Part (SI regulations live here)
        for child in body:
            if child.tag.removeprefix(NS) != "Part":
                _walk_or_p1(child, [title], result, True, None, "body")

    schedules_el = doc.find(NS + "Schedules")
    if schedules_el is not None:
        for sched in schedules_el.findall(NS + "Schedule"):
            sno = _schedule_number(sched)
            label = _heading(sched) or f"Schedule {sno}"
            keep = schedules is None or sno in schedules
            _walk(sched, [title, label], result, keep, sno, f"Schedule {sno}")
    return result


def _walk_or_p1(el: ET.Element, ctx: list[str], result: LegParseResult,
                in_scope: bool, sched_no: str | None, scope_label: str) -> None:
    if el.tag.removeprefix(NS) == "P1":
        result.p1_seen += 1
        if in_scope:
            _parse_p1(el, ctx, result, sched_no)
    else:
        _walk(el, ctx, result, in_scope, sched_no, scope_label)


def reconciliation_report(result: LegParseResult, source_name: str) -> str:
    lines = [
        f"# Reconciliation — {source_name} ({result.source})",
        "",
        f"Declared provisions (NumberOfProvisions): {result.declared_provisions}",
        f"Top-level P1 elements encountered:        {result.p1_seen}",
        f"Nested P1s (quoted amendment text, captured in parent): {result.p1_nested}",
        f"P1 elements in scope:                     {result.p1_in_scope}",
        f"Paragraph records emitted:                {len(result.records)}",
        "",
        f"P1 identity: top-level + nested = {result.p1_seen + result.p1_nested} "
        f"(declared: {result.declared_provisions}); "
        f"in-scope + skipped = "
        f"{result.p1_in_scope + sum(result.skipped_out_of_scope.values())} "
        f"(top-level: {result.p1_seen})",
        "",
        "## Out-of-scope P1s skipped (by container)",
    ]
    if result.skipped_out_of_scope:
        for label, count in sorted(result.skipped_out_of_scope.items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")
    lines += ["", "## Duplicate references — amendment versions (FIRST kept; "
              "in-force version is a human-review question)"]
    if result.duplicate_references:
        for ref, snippet in result.duplicate_references:
            lines.append(f"- {ref}: dropped alternate version — {snippet}")
    else:
        lines.append("- none")
    if result.reference_fallbacks:
        lines += ["", "## References derived from ids (no printed Pnumber)"]
        for pid in result.reference_fallbacks:
            lines.append(f"- {pid}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("xml", help="CLML source XML (ca06.xml / si2008_410.xml)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--part", help="Body Part filter, e.g. 15 (default: 15 for CA06)")
    ap.add_argument("--schedules", help="comma list, e.g. 1,5,7 (default: 1,5,7 for SI)")
    args = ap.parse_args()

    name = Path(args.xml).name
    part = args.part
    schedules = set(args.schedules.split(",")) if args.schedules else None
    if part is None and "ca06" in name:
        part = "15"
        if schedules is None:
            schedules = set()  # CA06 schedules out of scope (Part 15 only)
    if schedules is None and "si2008" in name:
        schedules = {"1", "5", "7"}

    result = parse_file(args.xml, part=part, schedules=schedules)
    write_jsonl(result.records, args.out)
    report = reconciliation_report(result, name)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    if result.p1_seen + result.p1_nested != result.declared_provisions:
        raise SystemExit(
            f"RECONCILIATION FAILURE: saw {result.p1_seen} top-level + "
            f"{result.p1_nested} nested P1s, declared {result.declared_provisions}")


if __name__ == "__main__":
    main()
