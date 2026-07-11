# RAG / Vector Retrieval Pattern (Sprint 5)

Read this before touching `app/rag/`, `workers/document_worker/`, or `workers/embedding_worker/`.

## Why this needs a real Supabase project, not just real Postgres

Sprint 3/4's RLS work only needed *any* real Postgres (a local portable install was enough) because RLS is a stock Postgres feature. Sprint 5 needs two extensions that are **not stock Postgres** and are not bundled with a vanilla community Postgres install: `vector` (pgvector) and `pgmq` (Supabase Queues). Confirmed empirically, not assumed: `SELECT name FROM pg_available_extensions WHERE name IN ('vector','pgmq')` returns zero rows against the local portable Postgres used for `backend/tests/rls/`, and both extensions are `available` (not yet installed) on the real Supabase project.

**Consequence:** any test that does real vector similarity search or real queue send/read/delete needs a real Supabase project's connection string, not just any Postgres. `backend/tests/rag/` documents and enforces this the same way `backend/tests/rls/` documents its own real-Postgres requirement.

SQLite (the fast local test stand-in) can still *create* a `knowledge_chunks` table with a `Vector` column (`pgvector`'s SQLAlchemy integration has a SQLite fallback), which is why unit/integration tests for chunking, embedding, and ingestion logic that don't need actual similarity search or actual queue operations still run against SQLite. Only `retrieval.search()`'s ordering and the queue send/read/delete round-trip need the real thing.

## The `postgres` (admin) vs `revnara_app` (app) split, for pgmq specifically

`revnara_app` (Sprint 3's dedicated non-bypassrls role) can `SELECT`/`INSERT`/`UPDATE`/`DELETE` on `knowledge_chunks` freely (it owns that table, having run the migration that created it) and can call `pgmq.send()`/`pgmq.read()`/`pgmq.delete()` on an *existing* queue. Whether it can call `pgmq.create()` (to make a *new* queue) turns out to depend on **who created the `pgmq` extension itself**, not on some fixed role limitation -- confirmed by actually testing both orderings, not assumed:

- On this project, the `postgres` admin role enabled `vector`/`pgmq` (`CREATE EXTENSION`) *before* `revnara_app` ever ran a migration against it. That makes `postgres` the extension's owner, and `pgmq.create()` requires being that owner -- so `revnara_app` gets `must be owner of extension pgmq` when it tries.
- Tested directly: if `revnara_app` itself is the one to run `CREATE EXTENSION IF NOT EXISTS pgmq` (e.g. a fresh database where nobody has enabled it yet), `revnara_app` becomes the owner and *can* then call `pgmq.create()` freely. This was confirmed empirically (`CREATE EXTENSION IF NOT EXISTS pg_trgm` succeeded directly as `revnara_app` against this project), not assumed from Postgres's general permission model.

Practically: `supabase/config/rag_queues.sql` (run once by the project's admin/`postgres` role, same shape as Sprint 4's Storage bucket provisioning) is what actually provisions the two queues **on this project specifically**, because the extension-ownership history here requires it. A genuinely fresh environment (e.g. CI, or a new Supabase project where the migration itself is the first thing to enable these extensions) may not need that admin step at all -- but running `rag_queues.sql` as an admin/superuser role is safe either way, since a real superuser bypasses the ownership check entirely regardless of who owns what.

## pgmq function overload gotcha

`pgmq.delete(queue_name, msg_id)` is overloaded (a single `bigint` vs. a `bigint[]` array). Calling it via asyncpg with plain untyped parameters raises `function pgmq.delete(unknown, unknown) is not unique` -- found by actually calling it, not from documentation. Every pgmq call in `app/rag/queue.py` uses explicit `CAST(:param AS type)` for this reason; don't remove the casts even though they look redundant.

## Classification/permission filtering is application-level, not RLS

`supabase/rls/knowledge_chunks.sql` follows the standard tenant-isolation template (see `docs/rls-pattern.md`) -- it enforces *tenant* isolation only. It deliberately does **not** try to enforce the `classification`/permission filter (a chunk marked `confidential` requires the caller to hold `company.manage`), because RLS session variables (`app.current_user_id`/`app.current_tenant_id`) don't carry the caller's permission set, only their identity and tenant. `app/rag/retrieval.py`'s `search()` is where that filter actually lives, as an explicit `WHERE classification IS DISTINCT FROM 'confidential'` clause when the caller lacks `company.manage` -- defense in depth alongside RLS, not a replacement for it, same relationship `scoped_to_tenant()` has with RLS everywhere else in this codebase.

Note the `IS DISTINCT FROM` rather than `!=`: a plain `classification != 'confidential'` silently **excludes** every row where `classification IS NULL` too (SQL's three-valued NULL comparison logic), which would have hidden every unclassified chunk from callers without `company.manage` -- the opposite of the intended behavior. Caught by reasoning through NULL semantics before shipping it, not by a failing test after the fact.

## Deletion propagation is application-level, not a DB cascade

`knowledge_chunks.source_type`/`source_id` is a polymorphic reference (a `files` row, a `portfolio_items` row, or a `case_studies` row) -- there is no single FK target for a `ON DELETE CASCADE` to attach to. `app/rag/ingestion.py`'s `delete_chunks_for_source()` is called explicitly from each of those three entities' delete endpoints instead.

## Idempotency: how "worker crash mid-batch, restart, no duplicate vectors" is actually true

Two mechanisms combine, not one:
1. `pgmq.read()`'s visibility timeout: a message being processed is invisible to other readers for `visibility_timeout_seconds`, but not deleted -- if the worker crashes before calling `pgmq.delete()`, the message reappears once the timeout elapses rather than being lost.
2. `knowledge_chunks`' unique constraint on `(tenant_id, source_type, source_id, chunk_index)`: the embedding worker `INSERT ... ON CONFLICT (...) DO UPDATE` on this constraint, so reprocessing the same chunk (because the message was redelivered) overwrites the same row instead of creating a duplicate one.

Neither alone is sufficient -- the visibility timeout alone would allow duplicate rows on redelivery, and the unique constraint alone doesn't help if messages are simply lost. See `backend/tests/rag/`'s worker crash-and-resume test for this proven end to end.
