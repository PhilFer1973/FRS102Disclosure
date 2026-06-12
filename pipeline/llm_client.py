"""Single client module for all Anthropic API calls.

Model routing, token logging, and per-run cost accounting live here and only
here (CLAUDE.md hard rule 10: cost accounting wired in from the first call).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import anthropic
from dotenv import load_dotenv

# Routing per CLAUDE.md: Haiku for fact resolution + classification,
# Sonnet for judgment + challenge + checklist drafting.
MODELS = {
    "classify": "claude-haiku-4-5",
    "draft": "claude-sonnet-4-6",
}

# USD per million tokens (input, output) — platform.claude.com pricing, 2026-06.
PRICES_USD_PER_MTOK = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}


@dataclass
class CallRecord:
    role: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class LLMClient:
    calls: list[CallRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        load_dotenv()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set (env or .env). Aborting before any spend.")
        self._client = anthropic.Anthropic()

    def complete_json(self, role: str, system: str, user: str, schema: dict,
                      max_tokens: int = 2000) -> dict:
        """One structured-output call; returns the parsed JSON object."""
        model = MODELS[role]
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        self._record(role, model, response)
        text = "".join(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    def _record(self, role: str, model: str, response: anthropic.types.Message) -> None:
        in_tok = response.usage.input_tokens
        out_tok = response.usage.output_tokens
        price_in, price_out = PRICES_USD_PER_MTOK[model]
        cost = (in_tok * price_in + out_tok * price_out) / 1_000_000
        self.calls.append(CallRecord(role, model, in_tok, out_tok, cost))

    def usage_summary(self) -> str:
        lines = ["## Token usage and cost", ""]
        by_model: dict[str, list[CallRecord]] = {}
        for c in self.calls:
            by_model.setdefault(c.model, []).append(c)
        lines.append("| Model | Calls | Input tokens | Output tokens | Cost (USD) |")
        lines.append("|---|---|---|---|---|")
        for model, calls in by_model.items():
            lines.append(
                f"| {model} | {len(calls)} | {sum(c.input_tokens for c in calls)} "
                f"| {sum(c.output_tokens for c in calls)} "
                f"| ${sum(c.cost_usd for c in calls):.4f} |")
        lines.append(
            f"| **total** | {len(self.calls)} "
            f"| {sum(c.input_tokens for c in self.calls)} "
            f"| {sum(c.output_tokens for c in self.calls)} "
            f"| **${self.total_cost_usd():.4f}** |")
        return "\n".join(lines)

    def total_cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)
