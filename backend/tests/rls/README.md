# RLS Tests

Requires a real Postgres connection, with Sprint 1-5's Alembic migrations and every `supabase/rls/*.sql` file applied, connected as a **non-superuser role** -- superusers bypass RLS (and `FORCE ROW LEVEL SECURITY`) entirely, which would make these tests pass for the wrong reason. This is the one thing in this repo that genuinely cannot be verified against SQLite. (Sprint 5's migration additionally needs the `vector`/`pgmq` extensions -- not available on a vanilla Postgres install at all, see `docs/rag-pattern.md` and `backend/tests/rag/README.md` for that separate requirement.)

Skipped automatically (with a clear reason) if `RLS_TEST_DATABASE_URL` isn't set -- these do not run as part of the default `pytest` invocation used by `tests/unit` and `tests/integration`.

## Running locally

```bash
# once, against any Postgres instance (a local portable install, Docker,
# or a real Supabase project's connection string):
createuser revnara_app          # or: CREATE ROLE revnara_app LOGIN;
createdb -O revnara_app revnara_rls_test

# apply schema + policies as that same non-superuser role:
DATABASE_URL=postgresql+asyncpg://revnara_app@<host>/revnara_rls_test alembic upgrade head
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/00_functions.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/organizations.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/users.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/workspaces.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/roles.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/permissions.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/role_permissions.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/organization_members.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/audit_events.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/skills.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/team_members.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/team_member_skills.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/portfolio_items.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/case_studies.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/files.sql
psql -U revnara_app -d revnara_rls_test -f ../../supabase/rls/knowledge_chunks.sql

# then run the suite:
RLS_TEST_DATABASE_URL=postgresql+asyncpg://revnara_app@<host>/revnara_rls_test pytest tests/rls -v
```

The `supabase/rls/*.sql` files are idempotent (`DROP POLICY IF EXISTS` before every `CREATE POLICY`), safe to re-run after a policy change without recreating the database.

## What this does NOT clean up

`conftest.py`'s `create_tenant` helper commits its test fixtures directly (a fresh Postgres transaction is required partway through, to change `SET LOCAL` context after the tenant's id is known -- see `docs/rls-pattern.md`'s "Bootstrap ordering"). Test data accumulates across runs rather than rolling back. Every test uses fresh random UUIDs specifically so leftover data from previous runs never affects assertions -- but if the test database grows large after many runs, just drop and recreate it; there is no meaningful state to preserve.

## In CI

`.github/workflows/backend-ci.yml`'s `rls-tests` job (DQ3.1) does exactly the setup above automatically, against a fresh Postgres service container, on every PR touching `supabase/` or `backend/app/*/models.py`.
