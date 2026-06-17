from evals.harness import run_eval


def test_gate_eval_clean_and_recall():
    r = run_eval()
    assert r["false_positives_clean"] == 0       # no findings on clean accounts
    assert r["recall"] == 1.0                     # every seeded defect caught
    assert dict(r["seeds"])["digit_misread"]      # OCR-style misread localised
    assert dict(r["seeds"])["break_balance"]      # balance failure caught
