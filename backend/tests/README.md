# Backend Tests

`tests/unit/` -- pure logic, no database.

`tests/integration/` -- exercises real FastAPI routes end to end, backed by
an in-memory SQLite database (`tests/conftest.py`'s `db_session`/`client`
fixtures) rather than Postgres.

**Why SQLite here:** no Docker/Postgres/Supabase project exists in the
environment these were first written in (see the Sprint 1/1.5 completion
notes). SQLite is a **local verification stand-in**, not the target
database -- it lets these tests actually run and catch real bugs today
instead of being written blind and left unverified. Postgres/Supabase
remains the real target (`supabase/README.md`), and `.github/workflows/backend-ci.yml`'s
`migration-check` job already runs Alembic against a real Postgres service
container in CI.

**Known gap this doesn't cover:** SQLite has no concept of row-level
security. Sprint 3's RLS-dependent tests (`tests/rls/`) cannot be
meaningfully verified against SQLite and require a real Postgres
connection -- do not add RLS tests to this SQLite-backed suite and
consider them equivalent to the real thing.

`tests/rls/` -- reserved for Sprint 3 onward; empty until a real Postgres
connection is available.

`tests/workers/` -- reserved for worker/queue tests, starting Sprint 5.
