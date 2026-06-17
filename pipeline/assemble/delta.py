"""Delta review (v1 feature): match findings across runs of one engagement.

Every re-run is a FULL review; the delta is a presentation layer over the
findings table, matched on identity_key:
  numerical: '<check_type>|<location>'   checklist: '<requirement_id>|<direction>'

Classification of the current run against the previous run:
  new        - identity present now, not in the previous run
  unchanged  - present in both
  resolved   - present previously, gone now
  regressed  - present now, and had been dispositioned 'resolved'/'accepted' in
               an earlier run (it came back after being dealt with)

Dispositions persist per engagement, so a regression is distinguishable from a
plain new finding.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeltaItem:
    identity_key: str
    status: str          # 'new' | 'unchanged' | 'resolved' | 'regressed'
    finding: dict        # the current finding (or the prior one, for 'resolved')


def compute_delta(current: list[dict], prior: list[dict],
                  resolved_keys: set[str] | None = None) -> list[DeltaItem]:
    resolved_keys = resolved_keys or set()
    cur = {f["identity_key"]: f for f in current}
    pri = {f["identity_key"]: f for f in prior}
    items: list[DeltaItem] = []
    for key, f in cur.items():
        if key in pri:
            items.append(DeltaItem(key, "unchanged", f))
        elif key in resolved_keys:
            items.append(DeltaItem(key, "regressed", f))
        else:
            items.append(DeltaItem(key, "new", f))
    for key, f in pri.items():
        if key not in cur:
            items.append(DeltaItem(key, "resolved", f))
    return items


def summarise(items: list[DeltaItem]) -> dict[str, int]:
    out = {"new": 0, "unchanged": 0, "resolved": 0, "regressed": 0}
    for it in items:
        out[it.status] += 1
    return out
