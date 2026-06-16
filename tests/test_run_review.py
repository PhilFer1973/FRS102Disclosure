"""Wiring test: intake JSON -> route -> FS JSON -> numerical gate, no DB."""

import json
from datetime import date
from pathlib import Path

from pipeline.intake.router import Accepted, route
from pipeline.validate.checks import validate
from pipeline.validate.fs_model import load_fs_json
from tests.test_router import profile  # reuse builder

FIX = Path(__file__).parent / "fixtures"


def test_sample_intake_is_accepted_pre_pr2024():
    d = json.loads((FIX / "sample_intake.json").read_text())
    assert d["framework"] == "FRS102"
    decision = route(profile(period_start=date.fromisoformat(d["period_start"]),
                             period_end=date.fromisoformat(d["period_end"])))
    assert isinstance(decision, Accepted) and decision.edition == "pre-PR2024"


def test_sample_accounts_unbalanced_is_caught():
    fs = load_fs_json(FIX / "sample_accounts.json")
    findings = validate(fs)
    # seeded defect: total equity casts to 1050 but net assets = 1000
    assert any(f.check_type == "cross_reference" and "balance" in f.description.lower()
               for f in findings)
    # and the equity cast itself is internally consistent (1050 = 100 + 950)
    assert not any(f.check_type == "cast" and "total_equity" in f.location
                   for f in findings)


def test_fs_json_round_trips_money_as_decimal():
    fs = load_fs_json(FIX / "sample_accounts.json")
    na = fs.statements["balance_sheet"].by_id()["net_assets"]
    assert str(na.current) == "1000"
