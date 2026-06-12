# FRS102Disclosure

Automated reviewer for UK FRS 102 financial statements. Upload a completed set of
accounts (PDF/Word/Excel); the system performs a full technical review and returns an
Excel issues register — missing disclosures, present-but-untriggered disclosures,
numerical errors, and formatting defects — every finding cited to FRS 102, the
Companies Act 2006, or SI 2008/410.

**Status: Phase 0 — corpus engineering.** See `CLAUDE.md` for the full project
specification, architecture, and build phases.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
copy .env.example .env   # then fill in keys
uv run pytest
```

## Layout

| Path | Contents |
|---|---|
| `corpus/` | Tier 1 requirements sources, Tier 2 explanatory corpus, Tier 3 eval set |
| `pipeline/` | Parsers, edition diff, checklist drafting, runtime pipeline stages |
| `graph/` | LangGraph graph, state, nodes, checkpointer config |
| `db/migrations/` | Numbered plain-SQL Supabase migrations |
| `review/` | Drafting batches in/out for human sign-off |
| `evals/` | Seeded-defect harness, golden datasets, metrics |
| `cli/` | Local end-to-end runner |
| `infra/` | Azure provisioning notes/scripts |
