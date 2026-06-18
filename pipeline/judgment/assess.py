"""Judgment layer (pipeline stage 7): RAG-grounded quality / R&M signals.

Runs a small set of judgment probes — recognition/measurement red flags and
disclosure-quality checks that the presence/numerical passes cannot see. Each
probe retrieves the relevant FRS 102 paragraphs (RAG) to ground its reasoning,
the model judges against the accounts narrative, and a finding is emitted ONLY
with a paragraph citation (CLAUDE.md: no citation, no finding). The challenge
pass can then re-verify each citation.

Probes are conservative: they fire only on a clear signal, else stay silent.
"""

from __future__ import annotations

from dataclasses import dataclass

from db.retrieve import retrieve
from pipeline.llm_client import LLMClient
from pipeline.validate.checks import Finding

JUDGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "issue_found": {"type": "boolean"},
        "finding": {"type": "string"},
        "citation": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["issue_found", "finding", "citation", "confidence"],
    "additionalProperties": False,
}

JUDGMENT_SYSTEM = """\
You are a senior UK chartered accountant reviewing a company's FRS 102 financial
statements for a specific recognition/measurement or disclosure-QUALITY issue.
You are given the accounts narrative and the relevant FRS 102 paragraphs.

Decide whether the specific issue is present in THESE accounts. Set
issue_found=true ONLY on a clear signal, and then:
- finding: a concise statement of the issue and why it matters.
- citation: the exact FRS 102 paragraph reference that governs it (from the
  paragraphs supplied). A finding WITHOUT a citation is invalid.
If there is no clear signal, set issue_found=false and leave finding/citation
empty. Do not speculate; a clean result is the right answer when unsure.
"""


@dataclass(frozen=True)
class Probe:
    key: str
    query: str            # retrieval query for grounding
    instruction: str      # what to look for


PROBES: list[Probe] = [
    Probe("goodwill_amortisation",
          "goodwill amortisation useful life impairment Section 19",
          "FRS 102 requires goodwill to be amortised over its finite useful life "
          "(and impaired). Flag if the accounts indicate goodwill is NOT amortised "
          "or is carried at cost without amortisation."),
    Probe("investment_property_measurement",
          "investment property fair value measurement Section 16",
          "Investment property must be measured at fair value through profit or "
          "loss where fair value can be measured reliably without undue cost. "
          "Flag if investment property is held at cost or depreciated cost."),
    Probe("policy_boilerplate",
          "accounting policies disclosure relevant to understanding",
          "Assess whether the accounting policies are entity-specific or are "
          "generic boilerplate that does not reflect the entity's actual "
          "transactions and balances. Flag clearly boilerplate/irrelevant policies. "
          "IMPORTANT: the accounts present TWO years, so a policy is only "
          "unnecessary if the related balance/transaction is immaterial in BOTH the "
          "current AND the prior year. If the item is material in either year shown, "
          "the policy is required - do not flag it. When you do flag a policy, say "
          "you have considered both years."),
    Probe("going_concern_proportionality",
          "going concern basis material uncertainty disclosure",
          "Assess whether the going concern disclosure is proportionate to the "
          "entity's position. Flag a bare boilerplate statement where the figures "
          "(e.g. losses, net current liabilities) suggest a fuller assessment is "
          "needed."),
    Probe("prior_period_restatement",
          "prior period error restatement comparative Section 10",
          "If the comparatives are labelled 'as restated' or a prior period "
          "adjustment has been made, FRS 102 Section 10 requires disclosure of the "
          "nature of the error and the amount of the correction for each line "
          "affected. Flag a restatement that lacks this explanatory note."),
    Probe("deferred_tax_recognition",
          "deferred tax timing differences recognition Section 29",
          "Deferred tax must be recognised on timing differences (e.g. accelerated "
          "capital allowances; tax losses only to the extent recoverable). Flag "
          "where the accounts suggest deferred tax has been omitted or a deferred "
          "tax asset recognised without evidence of recoverability."),
    Probe("dividends_distributable_reserves",
          "dividends distributable reserves profit and loss account",
          "Dividends may only be paid out of distributable profits. Flag where "
          "dividends are paid while the profit and loss reserve is negative or "
          "insufficient, indicating a possible unlawful distribution."),
    Probe("related_party_completeness",
          "related party transactions group undertakings disclosure Section 33",
          "Where the entity has a parent, subsidiaries or other related parties, "
          "FRS 102 Section 33 requires disclosure of related party transactions and "
          "outstanding balances. Flag where group undertakings clearly exist but "
          "related party disclosure is absent or merely boilerplate. DO NOT flag a "
          "validly-claimed para 33.1A exemption: a company that is a wholly-owned "
          "member of a group need not disclose transactions with other group members "
          "wholly owned within that group. 'Wholly owned' means the parent owns all "
          "the shares, and other group members that are 100% owned throughout the "
          "group also qualify. If the entity states it has taken this exemption and "
          "it appears wholly owned, that is correct — do not raise it."),
    Probe("depreciation_of_tangible_assets",
          "tangible fixed assets depreciation useful life Section 17",
          "Tangible fixed assets with a finite useful life must be depreciated. "
          "Flag where material tangible assets appear not to be depreciated, or the "
          "depreciation policy/useful lives are not disclosed."),
]


def assess_probe(probe: Probe, narrative: str, edition: str,
                 client: LLMClient) -> Finding | None:
    grounding = retrieve(probe.query, edition)
    para_text = "\n".join(f"[{ref}] {text}" for ref, text in grounding)
    user = (f"ISSUE TO ASSESS:\n{probe.instruction}\n\n"
            f"RELEVANT FRS 102 PARAGRAPHS:\n{para_text}\n\n"
            f"ACCOUNTS NARRATIVE:\n{narrative}")
    res = client.complete_json("judgment", JUDGMENT_SYSTEM, user, JUDGMENT_SCHEMA,
                               max_tokens=1500)
    if res["issue_found"] and res["citation"].strip():
        return Finding("judgment", f"FRS102 {res['citation']}",
                       f"{res['finding']} (confidence {res['confidence']:.2f})",
                       "standard-material")
    return None


def run_judgment(narrative: str, edition: str, client: LLMClient) -> list[Finding]:
    out = []
    for probe in PROBES:
        f = assess_probe(probe, narrative, edition, client)
        if f is not None:
            out.append(f)
    return out
