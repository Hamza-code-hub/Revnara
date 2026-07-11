# Supabase Project Configuration

This directory holds Supabase-managed configuration, kept separate from `backend/migrations/` (Alembic) per `docs/Revnara_Implementation_Plan.md` §6.

- `migrations/` — Supabase-managed SQL migrations (or a mirror of Alembic's generated SQL, per the team's eventual choice — record that decision as an ADR once made).
- `rls/` — Row-level security policy SQL, one file per table, following the pattern documented in `docs/rls-pattern.md` once Sprint 3 establishes it.
- `seeds/` — Local/staging seed data (`dev_seed.sql` etc.), introduced starting Sprint 2.
- `config/` — Supabase CLI project configuration, linking this repo to the `revnara-local`/`revnara-staging`/`revnara-prod` projects.

**Not yet initialized.** This requires the Supabase CLI (not installed in the environment this scaffold was created in) and real Supabase project credentials, both of which are Sprint 1 / §4 Environment Prerequisites tasks owned by the team lead:

```bash
# once the Supabase CLI is installed and you're logged in:
supabase init
supabase link --project-ref <revnara-staging-project-ref>
```

See `docs/Revnara_Sprint_Development_Plan.md` §4 for the full environment/account checklist.
