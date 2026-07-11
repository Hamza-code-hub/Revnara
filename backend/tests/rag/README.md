# RAG Tests

Requires a real Supabase project -- not just any real Postgres. Confirmed empirically (not assumed): `vector` and `pgmq` are `available` but not `installed` on the local portable Postgres used for `backend/tests/rls/`, meaning neither extension's binary is even present there. See `docs/rag-pattern.md` for the full explanation.

Skipped automatically (with a clear reason) if `RAG_TEST_DATABASE_URL` isn't set.

## Running locally

```bash
# Against the real Supabase project's connection string, as the
# revnara_app role (not the project's postgres/admin role -- these tests
# also exercise RLS, which the admin role's rolbypassrls=true would defeat):
DATABASE_URL=postgresql+asyncpg://revnara_app.<project-ref>@<host>/postgres alembic upgrade head
# Apply supabase/rls/knowledge_chunks.sql (and every other rls/*.sql file
# if starting fresh) as revnara_app.
# Run supabase/config/rag_queues.sql once as the project's admin/postgres
# role (queue creation needs pgmq extension-owner privilege -- revnara_app
# deliberately doesn't have it, see docs/rag-pattern.md).

RAG_TEST_DATABASE_URL=postgresql+asyncpg://revnara_app.<project-ref>@<host>/postgres pytest tests/rag -v
```

## What this does NOT clean up automatically

Same caveat as `backend/tests/rls/README.md`: `create_tenant`'s bootstrap commits directly (a fresh transaction is needed partway through to change session context), so cleanup is each test's own responsibility via `cleanup_tenant`, not an automatic rollback. Every test uses fresh random UUIDs so leftover data from a previous run never affects a later one, even if a test is interrupted before its own cleanup runs.

## Why some of these tests are slower than the rest of the suite

`test_worker_pipeline.py`'s crash-and-resume test waits out a real (short) pgmq visibility timeout to prove a message actually becomes redeliverable -- this is a real timing dependency on the actual queue mechanism, not simulated, so it takes a few real seconds rather than being instant like the rest of this repo's tests.
