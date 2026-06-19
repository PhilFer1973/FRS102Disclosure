from pipeline.extract.structure import note_numbers_present


def _layout(*contents):
    return {"paragraphs": [{"content": c} for c in contents]}


def test_detects_notes_without_a_period():
    # Teneo style: '4 Turnover' (no period after the number)
    lay = _layout("4 Turnover", "5 Employees",
                  "14 Creditors: amounts falling due within one year")
    assert note_numbers_present(lay) == ["4", "5", "14"]


def test_detects_notes_with_a_period():
    # FC style: '14. Debtors'
    assert note_numbers_present(_layout("1. General", "14. Debtors")) == ["1", "14"]


def test_movement_dates_are_not_read_as_notes():
    # statement-of-changes-in-equity date lines must not become note numbers
    lay = _layout("1 January 2024", "31 December 2024", "1 January 2023",
                  "2 Accounting policies")
    assert note_numbers_present(lay) == ["2"]


def test_sub_numbered_policy_items_excluded():
    assert note_numbers_present(_layout("2.17 Finance costs")) == []
