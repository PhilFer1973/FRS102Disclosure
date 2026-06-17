"""Checklist engine (pipeline stage 5): pure, deterministic, idempotent.

Evaluates the active requirements against an engagement's fact profile to decide,
for each, whether it APPLIES to these accounts. Edition-filtered (a rule applies
only if its edition matches the engagement's, or is 'both'). Three outcomes per
rule, from the trigger evaluation:

  applicable     - trigger fires: this disclosure is required for these accounts.
  not_applicable - trigger is false: not required (only surfaced for the
                   'untriggered'/present-but-not-required direction).
  undetermined   - a trigger fact is unresolved: route to the question queue.

Presence detection (is an applicable disclosure actually in the accounts?) is a
separate downstream step; this engine decides applicability only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.engine.conditions import evaluate, referenced_facts


@dataclass(frozen=True)
class Requirement:
    id: str
    source: str
    reference: str
    edition: str            # 'pre-PR2024' | 'PR2024' | 'both'
    requirement_text: str
    trigger_type: str       # 'always' | 'conditional' | 'encouraged'
    trigger_condition: str | None
    trigger_facts: tuple[str, ...]
    direction: str          # 'missing' | 'untriggered' | 'both'
    severity: str


@dataclass(frozen=True)
class EngineResult:
    requirement: Requirement
    outcome: str            # 'applicable' | 'not_applicable' | 'undetermined' | 'encouraged'
    missing_facts: tuple[str, ...] = field(default_factory=tuple)


def applies_to_edition(req_edition: str, engagement_edition: str) -> bool:
    return req_edition in ("both", engagement_edition)


def evaluate_requirement(req: Requirement, facts: dict[str, object]) -> EngineResult:
    if req.trigger_type == "encouraged":
        return EngineResult(req, "encouraged")
    if req.trigger_type == "always":
        return EngineResult(req, "applicable")
    # conditional
    if not req.trigger_condition:
        return EngineResult(req, "applicable")     # conditional w/o condition: be safe
    fires = evaluate(req.trigger_condition, facts)
    if fires is True:
        return EngineResult(req, "applicable")
    if fires is False:
        return EngineResult(req, "not_applicable")
    missing = tuple(sorted(referenced_facts(req.trigger_condition) - facts.keys()))
    return EngineResult(req, "undetermined", missing)


def run_checklist(requirements: list[Requirement], facts: dict[str, object],
                  engagement_edition: str) -> list[EngineResult]:
    return [evaluate_requirement(r, facts) for r in requirements
            if applies_to_edition(r.edition, engagement_edition)]


def required_facts(requirements: list[Requirement],
                   engagement_edition: str) -> set[str]:
    """Every fact the in-edition conditional rules need — the fact-profile
    builder's worklist."""
    out: set[str] = set()
    for r in requirements:
        if (applies_to_edition(r.edition, engagement_edition)
                and r.trigger_type == "conditional" and r.trigger_condition):
            out |= referenced_facts(r.trigger_condition)
    return out
