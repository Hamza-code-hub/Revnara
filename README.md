# Revnara

Governed AI for software-house business development.

## Chosen Stack

- Flutter + Dart for the app.
- Python + FastAPI for backend, AI agents, policies, integrations, and workers.
- Supabase for PostgreSQL, Auth, Storage, Realtime, pgvector, Queues, and Cron.
- Google Cloud Run for Python API and worker deployment.

See [docs/Revnara_Implementation_Plan.md](./docs/Revnara_Implementation_Plan.md) for the full implementation plan and [docs/Revnara_Sprint_Development_Plan.md](./docs/Revnara_Sprint_Development_Plan.md) for the sprint-by-sprint build plan the team is executing against.

## Architecture Rule

Flutter owns presentation. Python owns business authority and AI execution. Supabase owns managed data infrastructure.

## Repository Structure

```text
desktop/        Customer-facing Flutter app (Web, Windows, macOS, Linux; iOS/Android from Sprint 15.5)
admin-console/  Separate internal-staff Flutter app (Sprint 15.7) — own auth, own deploy
backend/        Python FastAPI app + workers
supabase/       Supabase migrations, RLS policies, seeds, CLI config
infrastructure/ Docker, Cloud Run configs
.github/        GitHub Actions CI/CD workflows
docs/           Architecture, planning, and sprint-development documents
```

## Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

**Desktop app:**

```bash
cd desktop
flutter pub get
flutter run -d windows \
  --dart-define=SUPABASE_URL=https://your-project.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=your-anon-key
  # or web-server / macos / linux
```

Without the `SUPABASE_URL`/`SUPABASE_ANON_KEY` dart-defines, the app still runs (useful for `/dev/gallery` or backend-only work) but the login screen shows a clear "Supabase is not configured" state instead of a sign-in form.

**The backend auto-starts when you run the desktop app** (debug builds only) — `flutter run` checks `/health`, and if nothing's there, launches `backend/.venv/.../python -m uvicorn app.main:app --reload` for you using the backend's own virtualenv, so you don't need a second terminal. Disable with `--dart-define=AUTO_START_BACKEND=false` if you're running the backend yourself with different flags, or don't have it set up locally (e.g. web builds skip this entirely, and it never runs in release builds).

Both projects currently run against no real database by default — the Supabase CLI and a provisioned Supabase project are required for real sign-in and any endpoint beyond `/health` (see `docs/Revnara_Sprint_Development_Plan.md` §4 Environment & Account Prerequisites). The backend test suite (`pytest`) runs against a local SQLite stand-in instead and does not require this setup — see `backend/tests/README.md`. Row-level security (`backend/tests/rls/`) is the one exception: SQLite has no RLS at all, so those tests need a real Postgres connection — see `backend/tests/rls/README.md` and `docs/rls-pattern.md`.

## Status

Sprint 1, 1.5 (Design System), 2 (Identity & Tenancy Backend), 3 (Authorization, RLS & Tenant Isolation Hardening), and 4 (Company Brain Data Model) are complete. Cross-tenant row-level security, the `require_permission` authorization dependency, fail-closed audit logging, tenant-aware rate limiting, and a global 403 handler are implemented and verified against a real local Postgres instance (not just SQLite) — see `docs/rls-pattern.md` for how and why. Sprint 4 adds tenant-scoped CRUD for the company profile (fields on `organizations` itself), team members, skills, portfolio items, and case studies, plus a `files` table and signed-upload flow backed by a `StorageProvider` abstraction (`SupabaseStorageProvider` is implemented but, like Sprint 2's Supabase Auth integration, not exercised end to end anywhere in this environment — there is no real Supabase project to call). Sprint 5 (Company Brain Retrieval / RAG) is next.
