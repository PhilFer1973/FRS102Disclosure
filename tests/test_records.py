import pytest

from pipeline.records import ParagraphRecord, normalize_text, read_jsonl, write_jsonl


def test_normalize_text_fixes_ligatures_and_whitespace():
    assert normalize_text("proﬁt  and\n loss") == "profit and loss"
    assert normalize_text("pre­tax") == "pretax"


def test_record_rejects_unknown_source_and_edition():
    with pytest.raises(ValueError):
        ParagraphRecord(source="IFRS", reference="1.1", edition="both", text="x")
    with pytest.raises(ValueError):
        ParagraphRecord(source="FRS102", reference="1.1", edition="2022", text="x")
    with pytest.raises(ValueError):
        ParagraphRecord(source="FRS102", reference="", edition="both", text="x")


def test_jsonl_round_trip(tmp_path):
    recs = [
        ParagraphRecord(source="FRS102", reference="4.1", edition="pre-PR2024",
                        text="An entity shall...", hierarchy=["FRS 102", "Section 4", "4.1"],
                        location="section_body", page=68),
    ]
    path = tmp_path / "out.jsonl"
    write_jsonl(recs, path)
    assert read_jsonl(path) == recs
