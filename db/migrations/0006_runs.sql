-- 0006: runs — one row per full review run of an engagement.
-- Re-runs are always full reviews; delta is a presentation layer over findings.

create table runs (
    id              uuid primary key default gen_random_uuid(),
    engagement_id   uuid not null references engagements (id) on delete cascade,
    sequence_no     integer not null,
    status          text not null default 'in_progress' check (status in
                        ('in_progress', 'awaiting_answers', 'complete', 'failed')),
    checkpoint_ref  text,
    assumptions     text[] not null default '{}',
    started_at      timestamptz not null default now(),
    completed_at    timestamptz,
    unique (engagement_id, sequence_no)
);
