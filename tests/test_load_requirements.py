from db.load_requirements import (
    apply_merges,
    build_merge_map,
    infer_value_type,
    triage_status,
)


def test_infer_value_type():
    assert infer_value_type("has_share_capital") == "boolean"
    assert infer_value_type("is_financial_institution") == "boolean"
    assert infer_value_type("applies_schedule1_para1A1") == "boolean"
    assert infer_value_type("number_of_employees") == "number"
    assert infer_value_type("turnover_amount") == "number"
    assert infer_value_type("period_end_date") == "date"
    assert infer_value_type("materiality_basis") == "text"


def test_merge_map_and_application():
    groups = [{"canonical": "applies_schedule1_para1A1",
               "members": ["applies_schedule1_para1A1",
                           "entity_applies_schedule1_para1A1",
                           "applies_schedule1_paragraph_1A1"]}]
    mm = build_merge_map(groups)
    assert mm["entity_applies_schedule1_para1A1"] == "applies_schedule1_para1A1"
    assert "applies_schedule1_para1A1" not in mm  # canonical maps to nothing

    row = {"trigger_facts": ["entity_applies_schedule1_para1A1", "has_share_capital"],
           "trigger_condition": "entity_applies_schedule1_para1A1 == false "
                                "AND has_share_capital == true"}
    merged = apply_merges(row, mm)
    assert merged["trigger_facts"] == ["applies_schedule1_para1A1", "has_share_capital"]
    assert "entity_applies_schedule1_para1A1" not in merged["trigger_condition"]
    assert "applies_schedule1_para1A1 == false" in merged["trigger_condition"]


def test_merge_dedupes_facts():
    groups = [{"canonical": "k", "members": ["k", "k_alt"]}]
    mm = build_merge_map(groups)
    row = {"trigger_facts": ["k", "k_alt"], "trigger_condition": "k == true"}
    assert apply_merges(row, mm)["trigger_facts"] == ["k"]


def test_triage_status():
    assert triage_status({"severity": "standard-material", "direction": "missing"}) \
        == "active"
    assert triage_status({"severity": "statutory", "direction": "missing"}) \
        == "in_review"
    assert triage_status({"severity": "standard-material", "direction": "untriggered"}) \
        == "in_review"
    assert triage_status({"severity": "standard-material", "direction": "both"}) \
        == "in_review"
