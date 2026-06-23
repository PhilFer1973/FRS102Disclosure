from decimal import Decimal

from pipeline.facts.builder import (
    accounts_context,
    build_fact_profile,
    compute_cashflow_presence,
    compute_departure_facts,
    compute_statement_presence,
)
from pipeline.llm_client import LLMTruncationError
from pipeline.validate.fs_model import FinancialStatements, LineItem, Statement

D = Decimal


def _fs():
    bs = Statement("balance_sheet", [
        LineItem("share_capital", "Called up share capital", D(206541), D(206541)),
        LineItem("net_assets", "Net assets", D(7843774), D(8056962)),
    ])
    return FinancialStatements("Four Communications Limited", "2024-12-31",
                               statements={"balance_sheet": bs})


def test_accounts_context_includes_entity_lines_and_notes():
    ctx = accounts_context(_fs(), ["14. Debtors", "22. Share capital"], "pre-PR2024")
    assert "Four Communications Limited" in ctx
    assert "pre-PR2024" in ctx
    assert "Called up share capital: 206,541" in ctx
    assert "14. Debtors" in ctx
    assert "balance sheet" in ctx  # underscores humanised


def test_compute_cashflow_presence_distinguishes_exemption_from_real_statement():
    # the exemption wording is not a cash flow statement
    assert compute_cashflow_presence(
        "The company is a qualifying entity and is exempt from preparing a "
        "statement of cash flows.") == {"presents_cash_flow_statement": False}
    # actual cash-flow-statement line items
    assert compute_cashflow_presence(
        "Net cash from operating activities 1,200; financing activities (300)."
    ) == {"presents_cash_flow_statement": True}


def test_compute_statement_presence_reads_what_is_there():
    p = compute_statement_presence(_fs(), "Statement of changes in equity ...")
    assert p["presents_balance_sheet"] is True
    assert p["presents_statement_of_changes_in_equity"] is True
    assert p["presents_income_statement"] is False  # no income statement here


def test_compute_departure_facts_restatement_is_not_a_departure():
    # a plain prior-period restatement is NOT a true-and-fair-override departure
    out = compute_departure_facts(
        "The 2023 comparatives have been restated to correct a prior period error.")
    assert out["has_prior_period_departure_affecting_current_amounts"] is False
    assert out["has_departure_from_company_law_accounting_principles"] is False
    # explicit override wording -> leave it to the resolver
    assert compute_departure_facts(
        "The directors have departed from a requirement of FRS 102 to give a "
        "true and fair view.") == {}


class _SplittingClient:
    """Fake LLM client: truncates any facts call carrying more than `cap` facts,
    so build_fact_profile must split the batch down to size to succeed."""

    def __init__(self, cap: int):
        self.cap = cap
        self.chunk_sizes: list[int] = []

    def complete_json(self, role, system, user, schema, max_tokens=2000):
        keys = [ln[2:].split(":")[0].strip()
                for ln in user.splitlines() if ln.startswith("- ")]
        self.chunk_sizes.append(len(keys))
        if len(keys) > self.cap:
            raise LLMTruncationError("simulated max_tokens truncation")
        return {"resolutions": [
            {"key": k, "value": "false", "confidence": 0.9, "reasoning": "x"}
            for k in keys]}


def test_build_fact_profile_splits_on_truncation():
    facts = {"is_lessee", "is_parent_entity", "uses_revaluation_model",
             "is_qualifying_entity"}
    client = _SplittingClient(cap=1)               # only single-fact calls succeed
    profile, resolutions = build_fact_profile(
        facts, {}, _fs(), [], "pre-PR2024", client, batch=4)
    # every requested fact was resolved despite the initial batch truncating
    for f in facts:
        assert f in profile
    assert max(client.chunk_sizes) > 1             # a big chunk was attempted
    assert client.chunk_sizes.count(1) >= len(facts)  # then split to singles
