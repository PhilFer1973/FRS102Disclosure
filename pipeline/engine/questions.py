"""Question loop (pipeline stage 6, V1 file-driven form).

After fact resolution, some requirements are undetermined because a trigger fact
could not be resolved from the accounts. This builds a bounded, prioritised set
of plain-English questions for the reviewer — each carrying provenance (which
requirements it resolves) — highest-leverage facts first (those that would
resolve the most requirements). Answers seed the fact profile on the next run,
collapsing undetermined requirements into applicable / not-applicable.

Until the LangGraph interrupt/checkpoint loop exists, answers are supplied via a
JSON file (fact_key -> true/false/value), so the loop is: run -> questions ->
answer file -> re-run.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pipeline.engine.checklist import EngineResult
from pipeline.llm_client import LLMClient

QGEN_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fact_key": {"type": "string"},
                    "topic": {"type": "string"},
                    "question": {"type": "string"},
                    "why": {"type": "string"},
                },
                "required": ["fact_key", "topic", "question", "why"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

QGEN_SYSTEM = """\
You prepare interview questions for a UK chartered accountant reviewing a
company's FRS 102 financial statements. Each fact below could not be determined
from the accounts and must be confirmed before the review is complete.

For each fact, produce THREE things:
- topic: a short plain-English heading for the area (2-4 words), e.g. "Group
  structure", "Leasing", "Going concern", "Dividends".
- question: ONE clear, conversational question a senior reviewer would put to the
  preparer, in plain English. NO FRS 102 jargon, NO paragraph numbers, NO
  fact-key names. The reviewer should be able to give a full answer in their own
  words.
- why: ONE short plain-English sentence explaining why it matters — what the
  answer changes about which disclosures are required.

Keep everything human and jargon-free. Do not invent facts.
"""


@dataclass
class Question:
    fact_key: str
    question_text: str
    affected_refs: tuple[str, ...]
    topic: str = ""
    why: str = ""

    @property
    def provenance(self) -> str:
        return "affects: " + ", ".join(self.affected_refs)


def undetermined_facts(results: list[EngineResult]) -> dict[str, set[str]]:
    """Unresolved fact -> set of source-qualified citations that need it.

    Citations are source-qualified (e.g. 'FRS102 29.20', 'CA06 s416(3)') so the
    reviewer can look each one up directly from the question row (Phil's rule:
    every question/issue carries its source paragraph)."""
    out: dict[str, set[str]] = defaultdict(set)
    for r in results:
        if r.outcome == "undetermined":
            req = r.requirement
            citation = f"{req.source} {req.reference}".strip()
            for f in r.missing_facts:
                out[f].add(citation)
    return out


def generate_questions(fact_provenance: dict[str, set[str]],
                       registry: dict[str, dict], client: LLMClient,
                       limit: int = 25) -> list[Question]:
    ranked = sorted(fact_provenance.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:limit]
    listing = "\n".join(
        f"- {key}: {registry.get(key, {}).get('description', key)} "
        f"(affects {len(refs)} requirements)" for key, refs in ranked)
    res = client.complete_json("facts", QGEN_SYSTEM,
                               f"Facts needing a question:\n{listing}",
                               QGEN_SCHEMA, max_tokens=4000)
    qmap = {q["fact_key"]: q for q in res["questions"]}
    out = []
    for key, refs in ranked:
        q = qmap.get(key, {})
        out.append(Question(key, q.get("question", f"Resolve fact: {key}?"),
                            tuple(sorted(refs)), topic=q.get("topic", ""),
                            why=q.get("why", "")))
    return out
