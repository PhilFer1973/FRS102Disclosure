-- 0008: questions — bounded iterative question rounds (hard cap 3 per run).
-- Each question carries provenance: which requirement/trigger it resolves and
-- why the document could not answer it.

create table questions (
    id             uuid primary key default gen_random_uuid(),
    run_id         uuid not null references runs (id) on delete cascade,
    round          integer not null check (round between 1 and 3),
    fact_key       text not null references fact_registry (key),
    question_text  text not null,
    provenance     text not null,
    answer         text,
    answered_at    timestamptz,
    created_at     timestamptz not null default now()
);

create index questions_run_idx on questions (run_id, round);
