# RLS Pattern (DB3.3)

Every future table's row-level security should follow this pattern. Read this before writing a new `supabase/rls/*.sql` file.

## Why RLS needs a real Postgres connection to verify

SQLite (the local backend test stand-in, `backend/tests/README.md`) has no concept of row-level security at all. `backend/tests/rls/` cannot run against it -- those tests require a real Postgres connection (local portable Postgres, Docker, or a real Supabase project). Everything else in this plan can be verified without one; RLS cannot.

## Why RLS needs session variables, not just `auth.jwt()`

Supabase's typical RLS pattern assumes queries go through PostgREST, where the authenticated user's JWT claims are automatically available to policies via `auth.uid()`/`auth.jwt()`. Revnara's architecture is different: the FastAPI backend connects to Postgres directly (via SQLAlchemy/asyncpg), and tenant resolution happens in the backend, not in the JWT itself (a user can belong to multiple organizations, so "tenant" is never a fixed JWT claim -- see `app/tenancy/middleware.py`).

This means RLS must read from **Postgres session-local variables that the backend sets explicitly**, not from `auth.jwt()`. Two variables:

| Variable | Set by | Meaning |
|---|---|---|
| `app.current_user_id` | Every authenticated request, as early as possible (`app/tenancy/pg_session.py`'s `set_pg_actor_context`) | The JWT-verified caller. Independent of tenant -- always available once authenticated. |
| `app.current_tenant_id` | Only once a single definite tenant context exists for the request (`resolve_tenant_context`, or explicitly during org-creation bootstrap) | The tenant this request is scoped to. **Not set** for endpoints that intentionally span tenants (`GET /me`) or before a tenant exists yet (creating a new organization). |

Both use `SET LOCAL`, scoped to the current transaction -- they reset automatically at commit/rollback, never leak across requests even on a pooled connection.

## Helper SQL functions (`00_functions.sql`)

```sql
CREATE OR REPLACE FUNCTION current_actor_user_id() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION is_member_of_tenant(check_tenant_id uuid) RETURNS boolean AS $$
  SELECT EXISTS (
    SELECT 1 FROM organization_members om
    WHERE om.tenant_id = check_tenant_id AND om.user_id = current_actor_user_id()
  )
$$ LANGUAGE sql STABLE;
```

`current_setting(..., true)` returns NULL if the variable was never set (rather than raising) -- combined with `NULLIF`, this means an unset variable makes every policy comparison evaluate to NULL/false. **Unset session state fails closed, it does not fail open.**

## The pattern, per table

1. `ALTER TABLE x ENABLE ROW LEVEL SECURITY;`
2. `ALTER TABLE x FORCE ROW LEVEL SECURITY;` -- **do not skip this.** By default Postgres RLS does not apply to a table's owner, and the backend's connection role is very likely that owner (it ran the migrations that created the table). Without `FORCE`, RLS would silently no-op for the exact connection it exists to protect.
3. A `SELECT` policy, generally: `tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id)` -- the first clause covers "I'm currently working in this tenant," the second covers "I have a real membership here even if it isn't my *current* tenant context" (used by `GET /me`).
4. `INSERT`/`UPDATE`/`DELETE` policies generally require `tenant_id = current_tenant_id()` specifically (not the `is_member_of_tenant` fallback) -- mutations should only happen within an established, current tenant context, never merely because a membership exists somewhere.
5. Exceptions, and there are a few real ones -- see below.

## Known exceptions (read before assuming every table fits the template above)

- **`organizations`** has no `tenant_id` column -- it *is* the tenant. Policies use `id` instead of `tenant_id`. `INSERT` is `WITH CHECK (true)`: creating a new organization never requires already belonging to one, and this is also the point in the org-creation bootstrap flow where `current_tenant_id()` genuinely cannot be set yet (the row doesn't have an id until after the insert).
- **`users`** is a global identity mirror (see its model docstring), not tenant-scoped at all. `SELECT`/`UPDATE` use `id = current_actor_user_id() OR EXISTS(membership in current tenant)` -- see your own profile always, see a teammate's profile only while you share a tenant context with them. `INSERT` is `WITH CHECK (id = current_actor_user_id())` -- you may only ever create your own profile row.
- **`permissions`** is a global, code-defined catalog (`app/organizations/permissions_catalog.py`), not tenant data. It gets RLS enabled with an open `SELECT` policy and deliberately **no** `FORCE ROW LEVEL SECURITY` -- migrations/seeds (running as the table owner) need to freely manage this catalog, and it contains no tenant-identifying information for a non-owner role to be protected from.
- **`role_permissions`** has no `tenant_id` column either (it's a pure join table). Policies reach through to the associated `roles` row's `tenant_id`.
- **`audit_events`** has no `UPDATE`/`DELETE` policies at all -- combined with `FORCE ROW LEVEL SECURITY`, this makes audit rows genuinely immutable through the application, not just immutable by convention.

## Bootstrap ordering (read this before adding a new "create X" endpoint)

Any endpoint that creates a brand-new tenant-defining row (today: only `POST /organizations`) needs to set `app.current_user_id` **before its first query** (so RLS's `is_member_of_tenant`/"is this my own row" fallbacks can pass), and set `app.current_tenant_id` **immediately after** the new tenant-defining row gets its id (so every subsequent insert in that same bootstrap -- default workspace, default roles, owner membership -- lands inside the correct, now-established tenant context). See `app/organizations/router.py`'s `create_organization` and `app/organizations/service.py`'s `create_organization` for the reference implementation -- copy this ordering exactly for any future bootstrap-style endpoint, don't improvise a new pattern per feature.

## Checklist for adding RLS to a new table

- [ ] `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` (unless the table is a global, non-tenant catalog like `permissions` -- justify the exception in the policy file's comments if so).
- [ ] `SELECT` policy covers both "current tenant" and, if relevant, "I have a real relationship to this row regardless of current tenant."
- [ ] `INSERT`/`UPDATE`/`DELETE` require the *current*, established tenant context -- not a looser membership check.
- [ ] If the table is created as part of a bootstrap flow (a brand-new tenant-defining row), confirm the actor/tenant `SET LOCAL` ordering matches the pattern above.
- [ ] A negative test added to `backend/tests/rls/` proving Tenant A cannot read/write Tenant B's rows in this table.
- [ ] `.github/workflows/backend-ci.yml`'s RLS job (DQ3.1) will fail the build if this table is missing RLS entirely -- don't rely only on remembering to add a policy file.
