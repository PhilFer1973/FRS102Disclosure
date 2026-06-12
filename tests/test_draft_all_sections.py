import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.draft_all_sections import pick_sections  # noqa: E402


def test_pick_sections_order_and_scope():
    families = ["1", "1A", "1AA", "1AC", "1AD", "2", "2A", "3", "4", "5",
                "12", "12A", "20", "23", "23A", "34", "34A", "35",
                "PBE3", "PBE34", "PBE34B"]
    picked = pick_sections(families)
    # exclusions
    assert "4" not in picked       # already piloted
    assert "1AD" not in picked     # RoI small entities out of scope
    assert not any(f.startswith("PBE") for f in picked)
    # core sections come first, ascending; appendix families after
    assert picked[:8] == ["1", "1A", "2", "2A", "3", "5", "12", "20"]
    core_end = picked.index("35")
    assert set(picked[core_end + 1:]) == {"1AA", "1AC", "12A", "23A", "34A"}
    # appendix families also ascend
    assert picked[core_end + 1:] == ["1AA", "1AC", "12A", "23A", "34A"]
