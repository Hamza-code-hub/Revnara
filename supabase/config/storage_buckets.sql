-- Sprint 4 (Company Brain, DB4.2): private bucket for tenant file uploads.
-- Run this once against a real Supabase project's database (via the
-- project's admin/postgres role), the same way supabase/rls/*.sql is
-- applied once migrations have run.

insert into storage.buckets (id, name, public)
values ('company-files', 'company-files', false)
on conflict (id) do nothing;

-- Why there is no per-tenant `storage.objects` RLS policy here (unlike
-- every table in supabase/rls/): Supabase Storage's own RLS convention
-- keys off `auth.jwt()`, but this backend's tenant model deliberately does
-- NOT put a single tenant_id in the JWT (see docs/rls-pattern.md's "Why
-- RLS needs session variables, not just auth.jwt()" -- a user can belong
-- to more than one organization, so the JWT alone never tells you which
-- one a given Storage request is for). A `storage.objects` policy written
-- against `auth.jwt()` would therefore be checking the wrong thing
-- entirely, the same architectural mismatch Sprint 2/3 already solved for
-- Postgres tables -- copying that pattern here isn't possible without
-- restructuring how Storage requests reach Postgres, which they don't:
-- signed uploads go straight from the client to Supabase Storage, never
-- through this backend's session-variable-setting connection at all.
--
-- Instead, this bucket is locked down entirely at the RLS layer -- no
-- policy grants `anon` or `authenticated` any access to it -- so the only
-- two ways to reach an object are:
--   1. The backend's own service-role key (app/files/storage.py's
--      SupabaseStorageProvider), which bypasses Storage RLS by design,
--      same as any other service-role Supabase call.
--   2. A signed upload/download URL for one specific object path, which
--      Supabase's Storage service validates independently of RLS (the
--      token itself is the capability, not a policy match).
-- Combined with app/files/storage.py's tenant-id path prefix
-- (build_tenant_storage_path) and filename sanitization (path traversal
-- denial), this is the two-layer defense DB4.2 calls for: the backend
-- controls which paths a signed URL can ever be issued for, and nothing
-- else can reach the bucket at all.

-- No `alter table storage.objects enable row level security` here --
-- Supabase itself owns and already manages RLS on storage.objects
-- (owned by their internal supabase_storage_admin role, not reachable
-- even from the project's own postgres/admin role). Deliberately no
-- CREATE POLICY statements for the company-files bucket either -- see
-- the comment above. Do not add a permissive policy here without
-- re-reading it first.
