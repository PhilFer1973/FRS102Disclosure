"""Challenge pass (pipeline stage 8): a single adversarial re-read that attacks
the draft findings before they ship.

For each finding that a required disclosure is MISSING (or unclear), an
independent adversarial pass tries to REFUTE it — to locate the disclosure in
the accounts. If it finds the disclosure, the finding was a false positive and
is discarded (flipped to 'present' with the evidence); otherwise the finding
stands. This is the precision backstop for the asymmetric-downside side of the
register (the spec attacks 'confirm immaterial' the same way).

A second, independent LLM pass with the opposite goal to the presence pass:
presence asks 'is it there?'; challenge asks 'prove it IS there'.
"""

from __future__ import annotations

from pipeline.engine.presence import PresenceResult
from pipeline.llm_client import LLMClient

CHALLENGE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "refuted": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["index", "refuted", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

CHALLENGE_SYSTEM = """\
You are challenging draft findings that say a required FRS 102 disclosure is
MISSING from a set of accounts. Your job is to REFUTE each finding by locating
the disclosure — or its clear substance — in the accounts narrative provided.

For each numbered finding:
- refuted = true if the disclosure IS present (quote the exact supporting text
  as evidence). The original finding was wrong.
- refuted = false if, after a careful search, the disclosure is genuinely not
  there. The finding stands.

Be rigorous and adversarial: actively try to find the disclosure before
concluding it is missing. But do not invent evidence — if the text does not make
the disclosure, refuted = false.
"""


def challenge_missing(to_challenge: list[PresenceResult], narrative: str,
                      client: LLMClient, batch: int = 15
                      ) -> tuple[list[PresenceResult], int]:
    """Re-verify 'absent'/'unclear' findings; returns (results, n_refuted).
    A refuted finding is flipped to 'present' with the challenger's evidence."""
    out: list[PresenceResult] = []
    refuted = 0
    for start in range(0, len(to_challenge), batch):
        chunk = to_challenge[start:start + batch]
        listing = "\n".join(
            f"{i}. [{p.requirement.requirement.reference}] "
            f"{p.requirement.requirement.requirement_text}"
            for i, p in enumerate(chunk))
        user = (f"ACCOUNTS NARRATIVE:\n{narrative}\n\n"
                f"FINDINGS TO CHALLENGE (claimed missing):\n{listing}")
        res = client.complete_json("challenge", CHALLENGE_SYSTEM, user,
                                   CHALLENGE_SCHEMA, max_tokens=4000)
        by_index = {r["index"]: r for r in res["results"]}
        for i, p in enumerate(chunk):
            r = by_index.get(i, {"refuted": False, "evidence": ""})
            if r["refuted"]:
                refuted += 1
                out.append(PresenceResult(p.requirement, "present",
                                          "Challenge located it: " + r["evidence"]))
            else:
                out.append(p)
    return out, refuted
