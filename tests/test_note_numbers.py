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


def test_split_heading_number_on_its_own_line():
    # Teneo notes 7/8: the number sits on its own line, title in the next paragraph
    lay = _layout("6 Directors", "7", "Operating (loss)/profit",
                  "8", "(a) Taxation on profit", "9 Dividends")
    assert note_numbers_present(lay) == ["6", "7", "8", "9"]


def test_split_heading_out_of_range_figures_rejected():
    # a stray 'figure + label' pair beyond the note range must NOT become a note
    lay = _layout("1 General", "2 Policies", "3 Turnover",
                  "98", "annual accounts", "55", "Other costs")
    assert note_numbers_present(lay) == ["1", "2", "3"]


def test_page_number_followed_by_running_header_not_a_note():
    lay = _layout("4 Turnover", "16",
                  "Teneo Strategy Limited Notes forming part of the financial statements")
    assert note_numbers_present(lay) == ["4"]
