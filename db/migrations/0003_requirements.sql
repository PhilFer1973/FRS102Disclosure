-- 0003: requirements — the disclosure checklist.
-- HARD RULE: only status='active' rows feed the checklist engine, and rows reach
-- 'active' ONLY via human review (Phil). Claude Code drafts, never activates.
-- The trigger below enforces that an activated row only references registered
-- fact keys; draft rows may carry proposed (unregistered) keys.

create table requirements (
    id                 uuid primary key default gen_random_uuid(),
    source             text not null check (source in ('FRS102', 'CA06', 'SI2008/410')),
    reference          text not null,
    edition            text not null check (edition in ('pre-PR2024', 'PR2024', 'both')),
    applies_to         text not null default 'all',
    requirement_text   text not null,
    trigger_type       text not null check (trigger_type in
                           ('always', 'conditional', 'encouraged')),
    trigger_condition  text,
    trigger_facts      text[] not null default '{}',
    direction          text not null check (direction in ('missing', 'untriggered', 'both')),
    severity           text not null check (severity in
                           ('statutory', 'standard-material', 'standard-immaterial-candidate')),
    review_notes       text,
    status             text not null default 'draft' check (status in
                           ('draft', 'in_review', 'active', 'rejected')),
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now(),
    constraint conditional_needs_condition
        check (trigger_type <> 'conditional' or trigger_condition is not null)
);

create index requirements_source_ref_idx on requirements (source, reference, edition);
create index requirements_status_idx on requirements (status);

-- Guard: a row may only become 'active' if every trigger fact is registered.
create or replace function requirements_check_facts_registered()
returns trigger language plpgsql as $$
declare
    missing text[];
begin
    if new.status = 'active' then
        select coalesce(array_agg(f), '{}') into missing
        from unnest(new.trigger_facts) as f
        where not exists (select 1 from fact_registry r where r.key = f);
        if array_length(missing, 1) is not null then
            raise exception 'cannot activate requirement %: unregistered trigger facts %',
                new.id, missing;
        end if;
    end if;
    new.updated_at := now();
    return new;
end $$;

create trigger requirements_activation_guard
    before insert or update on requirements
    for each row execute function requirements_check_facts_registered();
