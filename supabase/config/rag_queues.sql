-- Sprint 5 (Company Brain Retrieval / RAG, DB5.3): creates the
-- document_tasks and embedding_tasks Supabase Queues (pgmq). Run this
-- once against a real Supabase project's database, as the project's
-- admin/postgres role -- the same one-time-provisioning pattern as
-- storage_buckets.sql.
--
-- Why this can't be part of the Alembic migration or run by the app's own
-- revnara_app role: pgmq.create() requires ownership of the pgmq
-- extension itself (confirmed by actually calling it as revnara_app and
-- getting "must be owner of extension pgmq", not assumed from docs).
-- revnara_app deliberately isn't the extension owner -- only the
-- send/read/delete operations app/rag/queue.py performs at runtime need
-- to work as that role, not queue creation.

select pgmq.create('document_tasks');
select pgmq.create('embedding_tasks');

-- The app role needs to read/write the actual queue tables pgmq.create()
-- just made (and any pgmq creates in the future) -- granted here rather
-- than assumed, since schema-level grants alone were not sufficient (see
-- docs/rag-pattern.md).
grant usage on schema pgmq to revnara_app;
grant create on schema pgmq to revnara_app;
grant all on all tables in schema pgmq to revnara_app;
grant all on all sequences in schema pgmq to revnara_app;
grant execute on all functions in schema pgmq to revnara_app;
alter default privileges in schema pgmq grant all on tables to revnara_app;
alter default privileges in schema pgmq grant execute on functions to revnara_app;
