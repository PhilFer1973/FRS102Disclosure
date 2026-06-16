from datetime import date

from pipeline.intake.router import (
    Accepted,
    IntakeProfile,
    Rejected,
    detect_format,
    route,
)


def profile(**kw) -> IntakeProfile:
    base = dict(entity_name="Acme Ltd", period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31), framework="FRS102",
                entity_type="company", is_consolidated=False,
                early_adoption_pr2024=False)
    base.update(kw)
    return IntakeProfile(**base)


def test_in_scope_company_pre_pr2024():
    d = route(profile())
    assert isinstance(d, Accepted) and d.edition == "pre-PR2024"


def test_period_starting_2026_routes_to_pr2024():
    d = route(profile(period_start=date(2026, 1, 1), period_end=date(2026, 12, 31)))
    assert isinstance(d, Accepted) and d.edition == "PR2024"


def test_early_adoption_routes_to_pr2024():
    d = route(profile(early_adoption_pr2024=True))
    assert isinstance(d, Accepted) and d.edition == "PR2024"


def test_period_starting_2025_12_31_is_pre_pr2024():
    d = route(profile(period_start=date(2025, 12, 31), period_end=date(2026, 12, 30)))
    assert isinstance(d, Accepted) and d.edition == "pre-PR2024"


def test_reject_ifrs_frs101_frs105():
    for fw in ("IFRS", "FRS101", "FRS105", "unknown"):
        d = route(profile(framework=fw))
        assert isinstance(d, Rejected) and d.reason == "out_of_scope_framework"


def test_reject_consolidated():
    d = route(profile(is_consolidated=True))
    assert isinstance(d, Rejected) and d.reason == "out_of_scope_consolidated"


def test_reject_llp_and_charity():
    for et in ("llp", "charity", "other"):
        d = route(profile(entity_type=et))
        assert isinstance(d, Rejected) and d.reason == "out_of_scope_entity_type"


def test_reject_invalid_period():
    d = route(profile(period_start=date(2025, 12, 31), period_end=date(2025, 1, 1)))
    assert isinstance(d, Rejected) and d.reason == "invalid_period"


def test_detect_format_by_extension():
    assert detect_format("accounts.pdf") == "pdf"
    assert detect_format("accounts.docx") == "docx"
    assert detect_format("accounts.xlsx") == "xlsx"
    assert detect_format("accounts.txt") is None


def test_detect_format_by_magic_bytes():
    assert detect_format("x.pdf", b"%PDF-1.7\n") == "pdf"
    assert detect_format("x.xlsx", b"PK\x03\x04rest") == "xlsx"
    assert detect_format("x.docx", b"PK\x03\x04rest") == "docx"
    assert detect_format("x.bin", b"\x00\x01\x02") is None
