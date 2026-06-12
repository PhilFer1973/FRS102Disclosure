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
            "enum": ["disclosure", "presentation", "recognition_measurement",
                     "scope_transition", "other"],
        },
        "rationale": {"type": "string"},
    },
    "required": ["para_type", "rationale"],
    "additionalProperties": False,
}

CLASSIFY_SYSTEM = """\
You classify paragraphs of FRS 102 (UK GAAP) for a disclosure-checklist pipeline.

Assign exactly one para_type:
- disclosure: requires information to be given in the notes or within the
  financial statements (amounts, narrative, analyses).
- presentation: governs the format, structure, ordering or face-of-statement
  placement of items (e.g. "shall present line items in this order", "shall
  distinguish X from Y on the face of the statement").
- recognition_measurement: governs whether/when items are recognised or how
  they are measured.
- scope_transition: scope of the section, effective date, or transitional
  provisions.
- other: definitions, cross-references without their own requirement, guidance
  that imposes no requirement.

If a paragraph mixes categories, prefer disclosure over presentation, and
either of those over recognition_measurement. Keep rationale to one sentence.
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
- severity: 'statutory' where the requirement is materiality-blind company law
  OR restates / is directly underpinned by a Companies Act or Regulations
  requirement (e.g. balance sheet formats — reviewer decision, Section 4 pilot);
  'standard-material' for normal FRS 102 requirements; 'standard-immaterial-
  candidate' for items routinely immaterial.
- review_notes: one sentence flagging anything the human reviewer should check
  (judgement made, ambiguity, interaction with company law).

FACT KEY REUSE: a list of already-proposed fact keys may follow. If a condition
you need is semantically identical to an existing key, you MUST reuse that key
verbatim rather than inventing a new spelling. Only propose a new key when no
existing key covers the condition.
"""


def _families(reference: str) -> str:
    return reference.partition(".")[0]


def _known_fact_keys(exclude_jsonl: Path) -> set[str]:
    """Fact keys already proposed by previous section batches (build/section_*
    row files), so the drafter reuses them instead of inventing new spellings."""
    keys: set[str] = set()
    for path in Path("build").glob("section_*_rows.jsonl"):
        if path.resolve() == exclude_jsonl.resolve():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    keys.update(json.loads(line).get("trigger_facts", []))
    return keys


def _ref_sort_key(reference: str) -> list[tuple[int, str]]:
    """Natural ordering for ids like 4.1, 4.1A, 4.12 (numeric then letter suffix)."""
    key = []
    for part in reference.split("."):
        m = re.match(r"(\d+)(.*)", part)
        key.append((int(m.group(1)), m.group(2)) if m else (0, part))
    return key


def _load_para_types() -> dict[tuple[str, str], dict]:
    """(edition, reference) -> classification, from the bulk batch pass if run."""
    path = Path("build/para_types.jsonl")
    if not path.exists():
        return {}
    out: dict[tuple[str, str], dict] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                if row.get("para_type"):
                    out[(row["edition"], row["reference"])] = {
                        "para_type": row["para_type"],
                        "rationale": row.get("rationale", ""),
                    }
    return out


def run_section(section: str, out_md: Path, out_jsonl: Path,
                client: LLMClient | None = None) -> LLMClient:
    recs_2022 = {r.reference: r for r in read_jsonl("build/frs102_2022.jsonl")
                 if _families(r.reference) == section}
    recs_2024 = {r.reference: r for r in read_jsonl("build/frs102_2024.jsonl")
                 if _families(r.reference) == section}
    diff = {row["reference"]: row for row in
            (json.loads(line) for line in
             Path("build/edition_diff.jsonl").open(encoding="utf-8"))
            if row["family"] == section}

    client = client or LLMClient()
    para_types = _load_para_types()

    # --- Pass 1: classification ----------------------------------------------
    # Prefer the bulk batch pass (build/para_types.jsonl); fall back to inline
    # Haiku calls for anything not covered.
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
            lookup = ("pre-PR2024", ref) if edition == "both" else (edition, ref)
            cached = para_types.get(lookup)
            if cached is None:
                cached = client.complete_json(
                    "classify", CLASSIFY_SYSTEM,
                    f"Paragraph {ref} of FRS 102:\n\n{text}",
                    CLASSIFY_SCHEMA, max_tokens=300)
            classifications[(ref, edition)] = cached

    # --- Pass 2: drafting (Sonnet) for disclosure/presentation paragraphs ----
    drafted: list[dict] = []
    proposed_facts: dict[str, list[str]] = defaultdict(list)
    known_keys = _known_fact_keys(exclude_jsonl=out_jsonl)
    for (ref, edition), cls in classifications.items():
        if cls["para_type"] not in ("disclosure", "presentation"):
            continue
        text = (recs_2022 if edition != "PR2024" else recs_2024)[ref].text
        diff_note = f"Edition diff status for {ref}: {diff[ref]['status']}."
        keys_in_play = sorted(known_keys | set(proposed_facts))
        keys_note = ("Already-proposed fact keys (reuse where semantically "
                     "identical):\n" + "\n".join(f"- {k}" for k in keys_in_play)
                     if keys_in_play else "No fact keys proposed yet.")
        result = client.complete_json(
            "draft", DRAFT_SYSTEM,
            f"{diff_note}\nThis row set applies to edition: {edition}.\n\n"
            f"{keys_note}\n\n"
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
    return client


def _render_markdown(section, classifications, drafted, proposed_facts, client) -> str:
    lines = [
        f"# Section {section} — draft checklist rows (DRAFT)",
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
