"""Intake router (pipeline stage 1): deterministic scope gating + edition routing.

Locked scope (CLAUDE.md): single UK companies under full FRS 102, both editions.
Out of scope (router rejects with a reason): consolidated/group accounts,
FRS 101, IFRS, FRS 105 micro-entities, charities, LLPs.

Edition routing: PR2024 (Sept 2024) edition applies to periods beginning on or
after 1 Jan 2026, or earlier on detected early adoption; otherwise the
pre-PR2024 (Jan 2022) edition.

This module is the DETERMINISTIC core. Extracting the IntakeProfile from the
accounts (framework/consolidation/entity-type from the compliance statement) is
the one LLM-assisted intake step and lives elsewhere; routing stays pure and
testable so scope decisions are auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

PR2024_EFFECTIVE_FROM = date(2026, 1, 1)
SUPPORTED_FORMATS = {"pdf", "docx", "xlsx"}
_MAGIC = {
    b"%PDF": "pdf",
    b"PK\x03\x04": "zip",  # docx and xlsx are both zip containers
}


@dataclass(frozen=True)
class IntakeProfile:
    entity_name: str
    period_start: date
    period_end: date
    framework: str          # 'FRS102' | 'FRS101' | 'IFRS' | 'FRS105' | 'unknown'
    entity_type: str        # 'company' | 'llp' | 'charity' | 'other'
    is_consolidated: bool
    early_adoption_pr2024: bool = False


@dataclass(frozen=True)
class Accepted:
    entity_name: str
    period_start: date
    period_end: date
    edition: str            # 'pre-PR2024' | 'PR2024'


@dataclass(frozen=True)
class Rejected:
    reason: str
    detail: str


def route(profile: IntakeProfile) -> Accepted | Rejected:
    if profile.period_end <= profile.period_start:
        return Rejected("invalid_period",
                        f"period_end {profile.period_end} not after period_start "
                        f"{profile.period_start}")
    if profile.framework != "FRS102":
        return Rejected("out_of_scope_framework",
                        f"framework is {profile.framework}; only full FRS 102 is "
                        "in scope (FRS 101 / IFRS / FRS 105 are rejected)")
    if profile.is_consolidated:
        return Rejected("out_of_scope_consolidated",
                        "consolidated/group accounts are out of scope (single "
                        "companies only)")
    if profile.entity_type != "company":
        return Rejected("out_of_scope_entity_type",
                        f"entity type is {profile.entity_type}; only UK companies "
                        "are in scope (LLPs and charities are rejected)")
    edition = ("PR2024" if profile.early_adoption_pr2024
               or profile.period_start >= PR2024_EFFECTIVE_FROM
               else "pre-PR2024")
    return Accepted(profile.entity_name, profile.period_start,
                    profile.period_end, edition)


def detect_format(path: str, header: bytes | None = None) -> str | None:
    """Return 'pdf' | 'docx' | 'xlsx', or None if unsupported. Uses magic bytes
    when a header is supplied, falling back to the extension to disambiguate the
    two zip-based Office formats."""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if header is not None:
        for magic, kind in _MAGIC.items():
            if header.startswith(magic):
                if kind == "pdf":
                    return "pdf"
                return ext if ext in {"docx", "xlsx"} else None
        return None
    return ext if ext in SUPPORTED_FORMATS else None
