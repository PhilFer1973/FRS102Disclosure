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
                    "question": {"type": "string"},
                },
                "required": ["fact_key", "question"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

QGEN_SYSTEM = """\
You write questions for a UK chartered accountant reviewing a company's FRS 102
financial statements. Each fact below could not be determined from the accounts
and is needed to decide whether certain disclosures apply. For each fact key,
write ONE clear, professional question the reviewer can answer about the entity
or its accounts — phrased for a yes/no or short answer, specific to FRS 102.
Do not invent facts; just turn the key into a good question.
"""


@dataclass
class Question:
    fact_key: str
    question_text: str
    affected_refs: tuple[str, ...]

    @property
    def provenance(self) -> str:
        return "affects: " + ", ".join(self.affected_refs)


def undetermined_facts(results: list[EngineResult]) -> dict[str, set[str]]:
    """Unresolved fact -> set of requirement references that need it."""
    out: dict[str, set[str]] = defaultdict(set)
    for r in results:
        if r.outcome == "undetermined":
            for f in r.missing_facts:
                out[f].add(r.requirement.reference)
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
                               QGEN_SCHEMA, max_tokens=3000)
    qmap = {q["fact_key"]: q["question"] for q in res["questions"]}
    return [Question(key, qmap.get(key, f"Resolve fact: {key}?"),
                     tuple(sorted(refs))) for key, refs in ranked]
