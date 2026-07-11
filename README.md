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
flutter run -d windows   # or web-server / macos / linux
```

Both projects currently run against no real database — the Supabase CLI and a provisioned Supabase project are required for anything beyond the `/health` endpoint (see `docs/Revnara_Sprint_Development_Plan.md` §4 Environment & Account Prerequisites).

## Status

Sprint 1 (Stack Reset & Project Foundation) is in progress. See `docs/Revnara_Sprint_Development_Plan.md` for what's next.
