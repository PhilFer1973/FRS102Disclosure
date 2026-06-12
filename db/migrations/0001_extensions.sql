-- 0001: extensions
-- pgvector for paragraph embeddings; pgcrypto for gen_random_uuid on older PG.
-- NOTE: access model is service-key only (backend pipeline); no RLS policies are
-- defined in these migrations. Revisit before any user-facing data access.

create extension if not exists vector;
create extension if not exists pgcrypto;
