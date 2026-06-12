-- 0002: fact_registry — controlled vocabulary of facts about an engagement.
-- Every requirements.trigger_condition may ONLY reference keys registered here.
-- New keys are explicit proposals, reviewed like checklist rows.

create table fact_registry (
    key              text primary key,
    description      text not null,
    value_type       text not null check (value_type in
                         ('boolean', 'number', 'text', 'date', 'enum')),
    resolution_hint  text,
    created_at       timestamptz not null default now()
);
