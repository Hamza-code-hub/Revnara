# Supabase Project Configuration

Supabase is the **managed data platform** this product runs on: PostgreSQL, Auth, Storage, Realtime, pgvector, Queues, and Cron, all as one hosted service (`docs/Revnara_Implementation_Plan.md` §1). This directory is not application code — it's the configuration/policy layer specific to that managed platform, kept separate from `backend/` (the Python application that talks to it) for a clear reason: **one schema source of truth.**

## Where table schema lives

`backend/migrations/` (Alembic) is the **only** place table schema (`CREATE TABLE`, columns, indexes) is defined and changed. There is deliberately no separate `supabase/migrations/` — running two migration tools against the same database invites drift (a table created by one that the other doesn't know about). Alembic's migrations run directly against the Supabase project's Postgres connection string (`DATABASE_URL`), the same as they would against any Postgres database; Supabase being "managed" doesn't change how schema migrations work.

## What actually lives here

- `rls/` — Row-level security policy SQL, one file per table, applied *after* the corresponding Alembic migration creates the table (same PR, per `docs/Revnara_Sprint_Development_Plan.md` §2.2's "every table ships RLS in the same PR" rule). RLS policies are kept here rather than inside Alembic migrations so they're easy to find, diff, and audit as their own category — they're a governance artifact as much as a schema one.
- `seeds/` — Local/staging seed data (`dev_seed.sql` etc.), introduced starting Sprint 2.
- `config/` — Supabase CLI project configuration, linking this repo to the `revnara-local`/`revnara-staging`/`revnara-prod` projects (Auth provider settings, Storage bucket policy, etc. — platform configuration Alembic has no concept of). `storage_buckets.sql` (Sprint 4) provisions the private `company-files` bucket used by `app/files/storage.py`.

## Real project (Sprint 4 onward)

A real Supabase project (`nbnmlfsxtiivvvoxuhdr`, dev/local use) is connected as of Sprint 4 -- migrations, every `rls/*.sql` file, and `config/storage_buckets.sql` have all been applied against it, and the whole request path (real Supabase Auth sign-in -> JWKS-verified JWT -> Postgres via a dedicated non-bypassrls `revnara_app` role -> RLS-enforced tenant isolation -> real Storage upload) has been verified end to end against it, not just locally.

Two things worth knowing about this project's setup that aren't obvious from the SQL files alone:

- **The default `postgres` connection role has `rolbypassrls = true`** (even though it isn't a superuser) -- it silently bypasses every RLS policy, the same pitfall Sprint 3 hit locally. A dedicated `revnara_app` role (`LOGIN`, `NOSUPERUSER`, `NOBYPASSRLS`) was created and granted `CREATE`/`USAGE` on schema `public` plus `ALTER DEFAULT PRIVILEGES` (so future Alembic-created tables are automatically usable by it) -- this is the role the backend's `DATABASE_URL` actually connects as. Any admin-only task (Storage schema setup, role management) needs the project's `postgres` role instead, since `revnara_app` intentionally has no access to the `storage` schema.
- **This project uses asymmetric JWT signing (ECC P-256 via JWKS)**, not the legacy HS256 shared secret -- see `docs/adr/0007-jwt-verification.md`, now Final. `backend/app/auth/jwt.py` verifies against whichever the token's own `alg` header says, so this isn't a hardcoded assumption.

The Supabase CLI itself (`supabase init`/`supabase link`) is still not set up in this environment -- everything above was done via direct SQL against the project's Postgres connection and Supabase's REST/Admin APIs, which is equally valid but means `supabase/config/` has no CLI-generated project link file yet. See `docs/Revnara_Sprint_Development_Plan.md` §4 for the full environment/account checklist if that's still wanted.
