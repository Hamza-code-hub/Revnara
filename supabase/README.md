# Supabase Project Configuration

Supabase is the **managed data platform** this product runs on: PostgreSQL, Auth, Storage, Realtime, pgvector, Queues, and Cron, all as one hosted service (`docs/Revnara_Implementation_Plan.md` §1). This directory is not application code — it's the configuration/policy layer specific to that managed platform, kept separate from `backend/` (the Python application that talks to it) for a clear reason: **one schema source of truth.**

## Where table schema lives

`backend/migrations/` (Alembic) is the **only** place table schema (`CREATE TABLE`, columns, indexes) is defined and changed. There is deliberately no separate `supabase/migrations/` — running two migration tools against the same database invites drift (a table created by one that the other doesn't know about). Alembic's migrations run directly against the Supabase project's Postgres connection string (`DATABASE_URL`), the same as they would against any Postgres database; Supabase being "managed" doesn't change how schema migrations work.

## What actually lives here

- `rls/` — Row-level security policy SQL, one file per table, applied *after* the corresponding Alembic migration creates the table (same PR, per `docs/Revnara_Sprint_Development_Plan.md` §2.2's "every table ships RLS in the same PR" rule). RLS policies are kept here rather than inside Alembic migrations so they're easy to find, diff, and audit as their own category — they're a governance artifact as much as a schema one.
- `seeds/` — Local/staging seed data (`dev_seed.sql` etc.), introduced starting Sprint 2.
- `config/` — Supabase CLI project configuration, linking this repo to the `revnara-local`/`revnara-staging`/`revnara-prod` projects (Auth provider settings, Storage bucket policy, etc. — platform configuration Alembic has no concept of).

## Not yet initialized

This requires the Supabase CLI (not installed in the environment this scaffold was created in) and real Supabase project credentials — both Sprint 1 / §4 Environment Prerequisites tasks:

```bash
# once the Supabase CLI is installed and you're logged in:
supabase init
supabase link --project-ref <revnara-staging-project-ref>
```

See `docs/Revnara_Sprint_Development_Plan.md` §4 for the full environment/account checklist.
