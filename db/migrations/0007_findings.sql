-- 0007: findings — the issues register.
-- identity_key drives delta matching across runs:
--   checklist: (requirement_id, direction)
--   numerical: (check_type, statement_location)
--   judgment:  (topic, citation)

create table findings (
    id              uuid primary key default gen_random_uuid(),
    run_id          uuid not null references runs (id) on delete cascade,
    identity_key    text not null,
    category        text not null check (category in
                        ('checklist', 'numerical', 'formatting', 'judgment')),
    direction       text check (direction in ('missing', 'untriggered')),
    severity        text not null check (severity in
                        ('statutory', 'standard-material', 'standard-immaterial-candidate')),
    requirement_id  uuid references requirements (id),
    citation        text not null,
    reasoning       text not null,
    source_loc      text,
    status          text not null default 'open',
    disposition     text,
    created_at      timestamptz not null default now()
);

create index findings_run_idx on findings (run_id);
create index findings_identity_idx on findings (run_id, identity_key);
