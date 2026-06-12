-- 0004: paragraphs — tagged paragraph store backing RAG and citation verification.
-- One row per source paragraph per edition it appears in (parser output).
-- EMBEDDING DIMENSION: vector(1024) assumes Voyage AI voyage-3 embeddings.
-- *** Review before applying: changing dimension later requires a column rebuild. ***

create table paragraphs (
    id         uuid primary key default gen_random_uuid(),
    source     text not null check (source in ('FRS102', 'CA06', 'SI2008/410')),
    reference  text not null,
    edition    text not null check (edition in ('pre-PR2024', 'PR2024', 'both')),
    para_type  text check (para_type in
                   ('disclosure', 'presentation', 'recognition_measurement',
                    'scope_transition', 'other')),
    text       text not null,
    hierarchy  text[] not null default '{}',
    embedding  vector(1024),
    created_at timestamptz not null default now(),
    unique (source, reference, edition)
);

create index paragraphs_source_ref_idx on paragraphs (source, reference);

-- Vector index deliberately deferred: build an HNSW index AFTER bulk-loading
-- embeddings, e.g.:
--   create index paragraphs_embedding_idx on paragraphs
--       using hnsw (embedding vector_cosine_ops);
