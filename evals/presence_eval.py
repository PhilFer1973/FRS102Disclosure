"""Disclosure-recall eval for the presence pass (LLM-driven; run manually).

Measures the product's core promise — required-and-missing recall — on a small
synthetic, committable narrative (no client data). Baseline: every disclosure is
present. Then each disclosure's text is removed in turn; the removed one must
flip to 'absent' (recall) while the others stay 'present' (precision).

  uv run python -m evals.presence_eval     # ~a few cents of Haiku/Sonnet

Not a pytest test (it costs per run); the deterministic gate eval lives in
evals/harness.py and runs free in CI.
"""

from __future__ import annotations

from pipeline.engine.checklist import EngineResult, Requirement
from pipeline.engine.presence import check_presence
from pipeline.llm_client import LLMClient

# Synthetic disclosures, each a self-contained block keyed by requirement ref.
BLOCKS = {
    "3.9": "Going concern\nThe directors have assessed the company's ability to "
           "continue as a going concern and have a reasonable expectation that it "
           "has adequate resources to continue in operational existence for the "
           "foreseeable future. Accordingly they continue to adopt the going "
           "concern basis in preparing the financial statements.",
    "33.9": "Related party transactions\nDuring the year the company entered into "
            "transactions with its parent undertaking totalling £420,000 (2023: "
            "£310,000). Amounts owed to the parent at the year end were £95,000.",
    "4.12": "Share capital\nThe allotted, called up and fully paid share capital "
            "comprises 100,000 ordinary shares of £1 each (2023: 100,000).",
    "8.2": "Accounting policies\nThe principal accounting policies applied in the "
           "preparation of these financial statements are set out below. They "
           "have been applied consistently to all periods presented.",
}

REQUIREMENTS = {
    "3.9": "Disclose that the financial statements are prepared on the going "
           "concern basis and the directors' assessment.",
    "33.9": "Disclose related party transactions and outstanding balances with the "
            "parent undertaking.",
    "4.12": "Disclose the number and nominal value of allotted, called up and "
            "fully paid share capital.",
    "8.2": "Disclose the accounting policies applied in preparing the financial "
           "statements.",
}


def _applicable(ref: str) -> EngineResult:
    req = Requirement(ref, "FRS102", ref, "both", REQUIREMENTS[ref], "always",
                      None, (), "missing", "standard-material")
    return EngineResult(req, "applicable")


def narrative(exclude: str | None = None) -> str:
    return "\n\n".join(text for ref, text in BLOCKS.items() if ref != exclude)


def main() -> None:
    client = LLMClient()
    applicable = [_applicable(r) for r in BLOCKS]

    base = {p.requirement.requirement.reference: p.status
            for p in check_presence(applicable, narrative(), client)}
    print("baseline (all should be present):", base)

    recall_hits, precision_hits, total = 0, 0, 0
    for removed in BLOCKS:
        res = {p.requirement.requirement.reference: p.status
               for p in check_presence(applicable, narrative(exclude=removed), client)}
        removed_absent = res.get(removed) in ("absent", "unclear")
        others_present = all(res.get(r) == "present" for r in BLOCKS if r != removed)
        recall_hits += removed_absent
        precision_hits += others_present
        total += 1
        print(f"  removed {removed}: flagged={res.get(removed)} "
              f"(recall {'OK' if removed_absent else 'MISS'}); "
              f"others intact {'OK' if others_present else 'NO'}")

    print(f"\nrecall (removed disclosure detected absent): {recall_hits}/{total}")
    print(f"precision (others stay present): {precision_hits}/{total}")
    print("\n" + client.usage_summary())


if __name__ == "__main__":
    main()
