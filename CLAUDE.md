# FRS102Disclosure — FRS 102 Financial Statement Reviewer

## What this project is

An automated reviewer for UK FRS 102 financial statements. A user uploads a completed
set of accounts (PDF/Word/Excel); the system performs a full technical review and returns
an Excel issues register of findings: disclosures that are **missing**, disclosures that
are **present but not required** ("confirm immaterial"), **numerical errors**, and
**formatting/consistency defects** — every finding grounded in a citation to FRS 102,
the Companies Act 2006, or SI 2008/410.

The owner (Phil) is an ICAEW chartered accountant and acts as the human reviewer for all
accounting-content decisions. **Claude Code builds; Phil signs off accounting content.**

## Locked scope (do not expand without asking)

| Decision | Locked value |
|---|---|
| Entities | Single UK companies under **full FRS 102** (all sizes) |
| Out of scope (router rejects with reason) | Consolidated/group accounts, FRS 101, IFRS, FRS 105 micros, charities, LLPs |
| Editions | Both: Jan 2022 edition AND Sept 2024 (Periodic Review) edition, routed by period start date (PR2024 effective periods beginning 1 Jan 2026, early adoption detected from compliance statement) |
| Inputs | **V1: PDF only** (owner decision 2026-06 — no sample Word/Excel accounts available; .docx/.xlsx deferred post-V1). Spec target remains PDF + Word + Excel. |
| Review directions | Bidirectional: required-and-missing AND present-and-untriggered |
| Numerical checks | Full deterministic suite (see below) — **in code, never LLM** |
| Formatting review | Mechanical (code) + stylistic (LLM) |
| Front half | Strategic report / directors' report reviewed under CA06 + SI 2008/410 Sch 7 |
| Materiality | Computed benchmark default (5% PBT / 1% turnover / 1–2% gross assets by entity profile), user override, basis + override logged on engagement |
| Question rounds | Bounded iterative: round 1 after fact profile, round 2 after judgment layer, hard cap 3, then complete on stated assumptions (assumptions listed in register) |
| Delta review | v1 feature. Every re-run is a FULL review; delta is a presentation layer matching findings across runs (resolved / unchanged / new / regressed). Dispositions and fact answers persist per engagement |
| Output | Excel issues register + short chat summary |

## Architecture

### Corpus tiers (treat completely differently)

- **Tier 1 — requirements sources.** FRS 102 (both editions), CA06 Part 15, SI 2008/410
  Schedules 1, 5, 7. These are the ONLY sources that may populate the requirements
  (checklist) database. All are XML.
- **Tier 2 — explanatory corpus.** FRC factsheets (7), two top-firm illustrative
  accounts. RAG only, for LLM reasoning and user-facing explanations. **Never a source
  of requirements. Never cite illustrative accounts as authority** — they are style
  references, tagged with edition + entity size.
- **Tier 3 — evaluation set.** Real filed accounts from Companies House plus
  seeded-defect variants. Never enters retrieval.

### Runtime pipeline (LangGraph, single graph, 9 stages)

1. **Intake/router** (code + 1 LLM call): classify format, detect regime/edition from
   compliance statement + period dates, reject out-of-scope, create engagement record.
2. **Extraction** (code-heavy): Azure Document Intelligence Layout for PDF;
   python-docx/openpyxl for Word/Excel. Output = structured FS model: typed statement
   tables, notes inventory (number, title, mapped FRS 102 topic — topic mapping is the
   one LLM-assisted step), decomposed policies note, front-half text. Every element
   carries source coordinates (page/table/cell).
3. **Numerical validation gate** (pure code): full suite below. **Failed-check
   disambiguation rule:** a failed cast is either a genuine finding or an extraction
   misread. Low-confidence extractions on a failed check trigger targeted re-extraction
   of that region first; only a clean re-read that still fails becomes a finding.
4. **Fact profile builder** (code + LLM): resolve every key in the fact registry.
   Each fact stores value, source location, confidence, resolution method
   (deterministic | llm | user). Unresolved → question queue.
5. **Checklist engine** (pure code, idempotent, re-runnable in ms): both directions
   against requirements DB; merge with numerical + mechanical formatting findings into
   draft register.
6. **Question loop** (LangGraph interrupt → Postgres checkpoint → resume): plain-English
   questions, each carrying provenance (which requirement/trigger it resolves and why
   the document couldn't answer it).
7. **Judgment layer** (LLM, RAG-grounded, only on items flagged judgmental): policy
   quality (boilerplate vs entity-specific), R&M correctness signals (e.g. investment
   property at depreciated cost, goodwill not amortised), going concern proportionality,
   stylistic consistency. **No citation, no finding.**
8. **Challenge pass** (single adversarial LLM pass over the full draft register):
   verify each citation's text actually supports the finding (re-read the paragraph);
   attack "confirm immaterial" recommendations hardest; downgrade/discard anything
   indefensible.
9. **Assembly** (code): register to Supabase, Excel via openpyxl, summary + file link
   to front end. Full audit trail per finding: rule or prompt, facts used, source
   paragraph, source location in the accounts.

LangGraph state holds: run config, fact profile, findings register, question queue.
The FS model stays in Azure Blob — only a reference in state (checkpoints must not bloat).

### Numerical check suite (all deterministic code)

Casting of every statement and note; cross-cast notes→face; balance sheet balances /
net assets = equity; reserves articulation (opening equity + P&L + OCI − dividends =
closing, SoCIE internal agreement); cash flow reconciles to BS cash movement and opens
from P&L profit; movement tables roll (FA, provisions, deferred tax; NBV = cost − depn);
tax note (current + deferred = charge; ETR rec casts from correct PBT); debtors/creditors
analyses tie; front-half figures tie to accounts; comparatives match prior year if supplied.

### Formatting checks

Mechanical (code): note numbering sequential/no gaps; every cross-reference resolves to
an existing note on the right subject; units consistent (£ vs £'000); rounding uniform;
period labels/column headers consistent; date logic (directors' report ≤ audit report;
approval date consistent everywhere). Stylistic (LLM, judgment layer): terminology
consistency (turnover/revenue, stock/inventories — either is fine, mixing is not);
defined terms; policy ↔ actual-balances alignment (orphan policies are untriggered
disclosures and come from the checklist engine, not the LLM).

### Severity model (hard rule)

Three tiers: **statutory** (materiality-blind — e.g. s411 employee numbers, Sch 1
formats), **standard-material**, **standard-immaterial-candidate**. ONLY the third tier
may ever be framed "no specific requirement identified — confirm immaterial". Never
output "safe to delete". Materiality grades severity; it never waives statutory items.

## Database (Supabase Postgres + pgvector)

Core tables (migrations in `db/migrations/`, plain SQL):

```
requirements(id, source, reference, edition, applies_to, requirement_text,
             trigger_type, trigger_condition, trigger_facts[], direction,
             severity, review_notes, status)
  -- source: 'FRS102'|'CA06'|'SI2008/410'
  -- edition: 'pre-PR2024'|'PR2024'|'both'
  -- trigger_type: 'always'|'conditional'|'encouraged'
  -- direction: 'missing'|'untriggered'|'both'
  -- status: 'draft'|'in_review'|'active'|'rejected'
  -- HARD RULE: only status='active' rows feed the engine; rows reach 'active'
  --            ONLY via Phil's human review. Claude Code drafts, never activates.

paragraphs(id, source, reference, edition, para_type, text, embedding)
  -- para_type: 'disclosure'|'recognition_measurement'|'scope_transition'|'other'
  -- the tagged paragraph store backing RAG and citation verification

fact_registry(key, description, value_type, resolution_hint)
  -- controlled vocabulary. Every trigger_condition may ONLY reference registered
  -- keys. New keys are explicit proposals, reviewed like checklist rows.

engagements(id, entity_name, period_start, period_end, edition, materiality_basis,
            materiality_value, materiality_overridden, created_at)
facts(engagement_id, key, value, source_loc, confidence, resolution_method)
runs(id, engagement_id, sequence_no, status, checkpoint_ref, assumptions[])
findings(id, run_id, identity_key, category, direction, severity, requirement_id,
         citation, reasoning, source_loc, status, disposition)
  -- identity_key for delta matching:
  --   checklist: (requirement_id, direction)
  --   numerical: (check_type, statement_location)
  --   judgment:  (topic, citation) with challenge-pass confirmation of fuzzy pairs
questions(id, run_id, round, fact_key, question_text, provenance, answer, answered_at)
```

## Tech stack

Python 3.12. LangGraph + langgraph-checkpoint-postgres (→ Supabase). Anthropic API
direct: **Sonnet for judgment + challenge, Haiku for fact resolution + classification;
Batch API for bulk corpus passes**. Azure: Container Apps Jobs (consumption) for runs,
Blob (UK South) for files, Document Intelligence Layout for PDF, Key Vault for secrets.
openpyxl for the register. Front end: Copilot Studio agent → Power Automate → Blob
trigger (built LAST; a thin CLI drives the pipeline until then).

Conventions: `uv` for environment/deps; `ruff` + type hints; `pytest`; secrets via env
vars only (`.env.example` maintained, `.env` gitignored); all LLM calls behind a single
client module with model routing, token logging, and cost accounting per run.

## Repo structure

```
corpus/tier1/   frs102_2022.xml, frs102_2024.xml, ca06.xml, si2008_410.xml
corpus/tier2/   factsheets/, illustrative/
corpus/tier3/   eval set (gitignored if containing real client data)
pipeline/       parse_frs102.py, parse_legislation.py, diff_editions.py,
                draft_checklist.py, extract/, validate/, facts/, engine/,
                judgment/, challenge/, assemble/
graph/          LangGraph graph, state, nodes, checkpointer config
db/migrations/  numbered SQL files
review/         drafting batches in/out for Phil's sign-off
evals/          seeded-defect harness, golden datasets, metrics
cli/            local runner for end-to-end testing without Copilot
infra/          Azure provisioning notes/scripts
```

## Build phases — work in this order, stop at each checkpoint

**Phase 0 — corpus engineering** *(checkpoint: Phil reviews Section 4 pilot batch
before any further sections are drafted)*
1. Inspect actual XML structure of all Tier 1 files FIRST (schemas are not assumed —
   legislation.gov.uk CLML and FRC XML differ; write parsers against what is there).
2. Parse → paragraph records with full reference metadata → `paragraphs` table.
3. Edition diff: align FRS 102 2022 vs 2024 paragraph-by-paragraph; classify
   unchanged/amended/new/deleted; tag `edition`.
4. Classification pass (Haiku/Batch): para_type tagging.
5. Checklist drafting (LLM, batched BY SECTION): disclosure paragraphs → draft
   requirements rows. **Pilot = FRS 102 Section 4 only**, end-to-end, into `review/`.
   STOP for sign-off. Then proceed section by section, never starting section N+1
   until N's format issues are resolved.
6. Tier 2: chunk + embed factsheets and illustrative accounts (tagged by edition/size).

**Phase 1 — ingestion & fact profile** *(checkpoint: extraction accuracy demo on both
illustrative accounts + 3 Companies House filings)*
Document Intelligence integration, Word/Excel parsers, FS model schema, numerical
validation gate with re-extraction disambiguation, fact profile builder, CLI runner.

**Phase 2 — checklist engine + question loop** *(checkpoint: end-to-end run on
illustrative accounts via CLI, questions answered at the terminal)*

**Phase 3 — judgment + challenge layers** *(checkpoint: full register on eval set;
measure missing-recall and delete-precision)*

**Phase 4 — assembly, delta review, Copilot front end** *(checkpoint: live run from
Teams)*

**Evals are not a phase — they grow continuously from Phase 1.** Seeded-defect harness:
remove required notes, insert untriggered ones, break casts, misnumber notes, mix units.
Headline metrics: recall on missing-required (the product's core promise) and precision
on confirm-immaterial (the asymmetric-downside number).

## Hard rules for Claude Code

1. **Never let an LLM do arithmetic or any check that can be deterministic.**
2. **Never activate checklist rows** — draft to `review/`, status stays 'draft'.
3. **Requirements only from Tier 1; explanations may use Tier 2; Tier 3 never retrieved.**
4. Every judgment finding must carry a paragraph citation that the challenge pass
   re-verifies against the paragraph text.
5. Trigger conditions may only reference fact_registry keys; new keys are proposals.
6. "Confirm immaterial" framing only for the third severity tier; never "safe to delete".
7. Re-runs are always full reviews; delta is presentation.
8. Inspect real file structures (XML schemas, FS layouts) before writing parsers —
   no assumed schemas.
9. Ask Phil about anything that changes accounting content, scope, or the severity
   model. Decide autonomously on implementation detail within these constraints.
10. Keep per-run cost accounting wired in from the first LLM call.

## Environment notes

- Owner machine: Windows; source XML currently at
  `C:\Users\Philip\Downloads\FRS102Disclosure` — first task includes moving these into
  `corpus/` in the repo (https://github.com/PhilFer1973/FRS102Disclosure).
- Azure subscription, Supabase account, M365 Copilot Business licence all exist.
- Until Phase 4, everything runs locally via the CLI; Azure services (Document
  Intelligence, Blob) are called from local during development.
