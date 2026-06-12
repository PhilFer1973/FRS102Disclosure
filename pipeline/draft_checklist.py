"""Section-batched checklist drafting. Pilot scope: FRS 102 Section 4 only.

Two passes over a section's paragraphs (both editions, using the edition diff):
1. Classification (Haiku): para_type per paragraph. 'disclosure' covers both
   disclosure AND presentation requirements (Section 4 is presentation-heavy;
   the kickoff scope explicitly includes presentation paragraphs).
2. Drafting (Sonnet): for each paragraph classified 'disclosure', draft
   requirements rows — per edition where the diff says the text diverges.

Output: a human-reviewable markdown table in review/, plus a JSONL of rows.
Rows are DRAFTS. Nothing here ever writes status='active' (CLAUDE.md rule 2);
every proposed fact key is flagged NEW because the fact registry starts empty.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from pipeline.llm_client import LLMClient
from pipeline.records import read_jsonl

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "para_type": {
            "type": "string",
            "enum": ["disclosure", "recognition_measurement", "scope_transition", "other"],
        },
        "rationale": {"type": "string"},
    },
    "required": ["para_type", "rationale"],
    "additionalProperties": False,
}

CLASSIFY_SYSTEM = """\
You classify paragraphs of FRS 102 (UK GAAP) for a disclosure-checklist pipeline.

Assign exactly one para_type:
- disclosure: requires information to be disclosed, presented, or shown in the
  financial statements or notes. INCLUDES presentation/format requirements
  (e.g. "shall present line items in this order", "shall distinguish X from Y
  on the face of the statement").
- recognition_measurement: governs whether/when items are recognised or how
  they are measured.
- scope_transition: scope of the section, effective date, or transitional
  provisions.
- other: definitions, cross-references without their own requirement, guidance
  that imposes no requirement.

If a paragraph contains both recognition/measurement AND disclosure content,
choose disclosure. Keep rationale to one sentence.
"""

ROW_SCHEMA = {
    "type": "object",
    "properties": {
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_text": {"type": "string"},
                    "trigger_type": {
                        "type": "string",
                        "enum": ["always", "conditional", "encouraged"],
                    },
                    "trigger_condition": {"type": ["string", "null"]},
                    "trigger_facts": {"type": "array", "items": {"type": "string"}},
                    "direction": {
                        "type": "string",
                        "enum": ["missing", "untriggered", "both"],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["statutory", "standard-material",
                                 "standard-immaterial-candidate"],
                    },
                    "review_notes": {"type": "string"},
                },
                "required": ["requirement_text", "trigger_type", "trigger_condition",
                             "trigger_facts", "direction", "severity", "review_notes"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["rows"],
    "additionalProperties": False,
}

DRAFT_SYSTEM = """\
You draft disclosure-checklist rows from FRS 102 paragraphs for a UK statutory
accounts reviewer. The reviewer checks single UK companies applying full FRS 102.

For the given paragraph, produce one row per distinct checkable requirement
(usually one; split only when the paragraph imposes clearly separable
requirements). Fields:

- requirement_text: concise imperative restatement of what must be presented or
  disclosed. Stay faithful to the paragraph; do not import requirements from
  other paragraphs.
- trigger_type: 'always' if it applies to every set of accounts; 'conditional'
  if it applies only when a condition holds; 'encouraged' if the paragraph
  encourages rather than requires.
- trigger_condition: for conditional rows, a boolean expression over snake_case
  fact keys, e.g. "has_investment_property == true". Null for always/encouraged.
- trigger_facts: every fact key used in trigger_condition (empty list if null).
  Keys are snake_case, generic, reusable across sections (e.g. has_intangibles,
  presents_separate_income_statement). Invent the minimal set needed.
- direction: 'missing' = flag when required but absent; 'untriggered' = flag
  when present but the trigger is false; 'both' where each applies.
- severity: 'statutory' ONLY where the requirement is materiality-blind company
  law (rare for FRS 102 text itself); 'standard-material' for normal FRS 102
  requirements; 'standard-immaterial-candidate' for items routinely immaterial.
- review_notes: one sentence flagging anything the human reviewer should check
  (judgement made, ambiguity, interaction with company law).

The fact registry is currently EMPTY: every fact key you use is a new proposal.
"""


def _families(reference: str) -> str:
    return reference.partition(".")[0]


def _ref_sort_key(reference: str) -> list[tuple[int, str]]:
    """Natural ordering for ids like 4.1, 4.1A, 4.12 (numeric then letter suffix)."""
    key = []
    for part in reference.split("."):
        m = re.match(r"(\d+)(.*)", part)
        key.append((int(m.group(1)), m.group(2)) if m else (0, part))
    return key


def run_section(section: str, out_md: Path, out_jsonl: Path) -> None:
    recs_2022 = {r.reference: r for r in read_jsonl("build/frs102_2022.jsonl")
                 if _families(r.reference) == section}
    recs_2024 = {r.reference: r for r in read_jsonl("build/frs102_2024.jsonl")
                 if _families(r.reference) == section}
    diff = {row["reference"]: row for row in
            (json.loads(line) for line in
             Path("build/edition_diff.jsonl").open(encoding="utf-8"))
            if row["family"] == section}

    client = LLMClient()

    # --- Pass 1: classification (Haiku) -------------------------------------
    # Classify each distinct (reference, text) once: unchanged paragraphs get a
    # single call; amended ones get one call per edition.
    classifications: dict[tuple[str, str], dict] = {}  # (ref, edition) -> result
    for ref in sorted(diff, key=_ref_sort_key):
        status = diff[ref]["status"]
        variants: list[tuple[str, str]] = []  # (edition_label, text)
        if status in ("unchanged",):
            variants = [("both", recs_2022[ref].text)]
        elif status == "amended":
            variants = [("pre-PR2024", recs_2022[ref].text),
                        ("PR2024", recs_2024[ref].text)]
        elif status == "deleted":
            variants = [("pre-PR2024", recs_2022[ref].text)]
        else:  # new
            variants = [("PR2024", recs_2024[ref].text)]
        for edition, text in variants:
            result = client.complete_json(
                "classify", CLASSIFY_SYSTEM,
                f"Paragraph {ref} of FRS 102:\n\n{text}",
                CLASSIFY_SCHEMA, max_tokens=300)
            classifications[(ref, edition)] = result

    # --- Pass 2: drafting (Sonnet) for disclosure paragraphs ------------------
    drafted: list[dict] = []
    proposed_facts: dict[str, list[str]] = defaultdict(list)
    for (ref, edition), cls in classifications.items():
        if cls["para_type"] != "disclosure":
            continue
        text = (recs_2022 if edition != "PR2024" else recs_2024)[ref].text
        diff_note = f"Edition diff status for {ref}: {diff[ref]['status']}."
        result = client.complete_json(
            "draft", DRAFT_SYSTEM,
            f"{diff_note}\nThis row set applies to edition: {edition}.\n\n"
            f"Paragraph {ref} of FRS 102 (Section {section}):\n\n{text}",
            ROW_SCHEMA, max_tokens=2000)
        for row in result["rows"]:
            row.update({"source": "FRS102", "reference": ref, "edition": edition,
                        "status": "draft"})
            drafted.append(row)
            for key in row["trigger_facts"]:
                proposed_facts[key].append(ref)

    # --- Output ---------------------------------------------------------------
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as fh:
        for row in drafted:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    md = _render_markdown(section, classifications, drafted, proposed_facts, client)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    print(md)


def _render_markdown(section, classifications, drafted, proposed_facts, client) -> str:
    lines = [
        f"# Section {section} — draft checklist rows (PILOT)",
        "",
        "Status of every row below: **draft**. Nothing is active until Phil reviews.",
        "All trigger fact keys are **NEW** proposals (fact registry is empty).",
        "",
        "## Classification (para_type)",
        "",
        "| Reference | Edition | para_type | Rationale |",
        "|---|---|---|---|",
    ]
    for (ref, edition), cls in classifications.items():
        lines.append(f"| {ref} | {edition} | {cls['para_type']} | {cls['rationale']} |")

    lines += [
        "",
        f"## Draft checklist rows ({len(drafted)})",
        "",
        "| Reference | Edition | Requirement | Trigger type | Trigger condition "
        "| Trigger facts | Direction | Severity | Review notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in drafted:
        facts = ", ".join(f"{k} (NEW)" for k in row["trigger_facts"]) or "—"
        cond = row["trigger_condition"] or "—"
        lines.append(
            f"| {row['reference']} | {row['edition']} | {row['requirement_text']} "
            f"| {row['trigger_type']} | {cond} | {facts} | {row['direction']} "
            f"| {row['severity']} | {row['review_notes']} |")

    lines += ["", f"## Proposed fact registry keys ({len(proposed_facts)}, all NEW)", ""]
    lines.append("| Key | Used by |")
    lines.append("|---|---|")
    for key in sorted(proposed_facts):
        lines.append(f"| {key} | {', '.join(sorted(set(proposed_facts[key])))} |")

    lines += ["", client.usage_summary(), ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--section", default="4")
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--out-jsonl", default=None)
    args = ap.parse_args()
    sec = args.section
    label = f"{int(sec):02d}" if sec.isdigit() else sec
    out_md = Path(args.out_md or f"review/section_{label}_draft.md")
    out_jsonl = Path(args.out_jsonl or f"build/section_{label}_rows.jsonl")
    run_section(sec, out_md, out_jsonl)


if __name__ == "__main__":
    main()
