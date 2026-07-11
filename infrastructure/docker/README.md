# Local Docker Setup

`docker-compose.yml` here is a **minimal Postgres + API stack** for local backend development before the Supabase CLI is set up. It is not a substitute for the real local Supabase stack.

Once the Supabase CLI is installed (see `supabase/README.md`), prefer `supabase start` for local development — it runs Postgres, Auth, Storage, Realtime, and Studio together and is what Sprint 1's exit criteria actually assume. This compose file remains useful for CI and for anyone who wants a lighter-weight Postgres-only loop while working purely on backend logic that doesn't touch Auth/Storage/Realtime.

**Not yet tested in this environment** — Docker is not installed on the machine this scaffold was created on. Verify `docker compose up` actually builds and starts cleanly before relying on it.
