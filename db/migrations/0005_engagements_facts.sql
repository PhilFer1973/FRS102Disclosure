-- 0005: engagements and their resolved facts.

create table engagements (
    id                      uuid primary key default gen_random_uuid(),
    entity_name             text not null,
    period_start            date not null,
    period_end              date not null,
    edition                 text not null check (edition in ('pre-PR2024', 'PR2024')),
    materiality_basis       text,
    materiality_value       numeric,
    materiality_overridden  boolean not null default false,
    created_at              timestamptz not null default now(),
    constraint period_valid check (period_end > period_start)
);

create table facts (
    engagement_id      uuid not null references engagements (id) on delete cascade,
    key                text not null references fact_registry (key),
    value              jsonb not null,
    source_loc         text,
    confidence         real check (confidence between 0 and 1),
    resolution_method  text not null check (resolution_method in
                           ('deterministic', 'llm', 'user')),
    resolved_at        timestamptz not null default now(),
    primary key (engagement_id, key)
);
