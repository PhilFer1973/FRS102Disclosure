from pipeline.engine.presence import gather_narrative


def test_gather_narrative_joins_paragraph_text():
    layout = {"paragraphs": [
        {"content": "1. General information\nThe company is..."},
        {"content": "Going concern\nThe directors have a reasonable expectation..."},
        {"content": ""},
        {},
    ]}
    text = gather_narrative(layout)
    assert "General information" in text
    assert "Going concern" in text
    assert text.count("\n") >= 1
