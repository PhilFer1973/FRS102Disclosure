import pytest

from pipeline.engine.conditions import evaluate, parse, referenced_facts


def test_simple_equality():
    assert evaluate("has_share_capital == true", {"has_share_capital": True}) is True
    assert evaluate("has_share_capital == true", {"has_share_capital": False}) is False
    assert evaluate("has_share_capital == false", {"has_share_capital": False}) is True


def test_bare_fact_is_truthy():
    assert evaluate("has_accounting_policy_changes",
                    {"has_accounting_policy_changes": True}) is True
    assert evaluate("has_accounting_policy_changes",
                    {"has_accounting_policy_changes": False}) is False


def test_not_operator():
    assert evaluate("NOT presents_separate_income_statement",
                    {"presents_separate_income_statement": False}) is True
    assert evaluate("not is_small_entity_republic_of_ireland",
                    {"is_small_entity_republic_of_ireland": True}) is False


def test_and_or_mixed_case_and_symbols():
    facts = {"is_qualifying_entity": True, "is_financial_institution": False,
             "is_individual_financial_statements": True}
    assert evaluate("is_qualifying_entity == true and is_financial_institution == "
                    "false and is_individual_financial_statements == true", facts) is True
    assert evaluate("is_lessee == true && has_applied == true",
                    {"is_lessee": True, "has_applied": True}) is True
    assert evaluate("a == true OR b == true", {"a": False, "b": True}) is True


def test_three_valued_unknown():
    # unknown fact -> None, unless short-circuited
    assert evaluate("a == true", {}) is None
    assert evaluate("a == true AND b == true", {"a": False}) is False   # short-circuit
    assert evaluate("a == true AND b == true", {"a": True}) is None     # b unknown
    assert evaluate("a == true OR b == true", {"a": True}) is True      # short-circuit
    assert evaluate("a == true OR b == true", {"a": False}) is None     # b unknown


def test_not_with_unknown():
    assert evaluate("NOT a", {}) is None


def test_parentheses():
    facts = {"a": False, "b": True, "c": True}
    assert evaluate("a == true OR (b == true AND c == true)", facts) is True
    assert evaluate("(a == true OR b == true) AND c == false",
                    {"a": False, "b": True, "c": True}) is False


def test_complex_real_condition():
    cond = ("NOT presents_separate_income_statement AND NOT "
            "presents_statement_of_income_and_retained_earnings")
    assert evaluate(cond, {"presents_separate_income_statement": False,
                           "presents_statement_of_income_and_retained_earnings": False}) is True
    assert evaluate(cond, {"presents_separate_income_statement": True,
                           "presents_statement_of_income_and_retained_earnings": False}) is False


def test_referenced_facts():
    assert referenced_facts("a == true AND NOT b OR c == false") == {"a", "b", "c"}


def test_malformed_raises():
    with pytest.raises(ValueError):
        parse("a == == b")
