-- Sprint 2 dev/staging seed data (DB2.3): 2 organizations, 2 workspaces
-- each, a handful of users/roles -- needed as the fixture base for
-- Sprint 3's cross-tenant isolation tests.
--
-- Run against a real Postgres/Supabase database that already has Sprint
-- 1-2's Alembic migrations applied (backend/migrations/). This file is
-- NOT run by the SQLite-backed backend test suite (tests/conftest.py
-- seeds its own minimal fixtures per test instead) -- it's for local
-- Supabase development and the CI migration-check job's seed-validity
-- smoke test (.github/workflows/backend-ci.yml).
--
-- Not yet executed against a real database in the environment this was
-- authored in (no Supabase project provisioned yet -- see §4 Environment
-- Prerequisites). Review before first real use.

begin;

-- Tenant A: Acme Software
insert into organizations (id, name, created_at, updated_at, version, legal_hold)
values ('11111111-1111-1111-1111-111111111111', 'Acme Software', now(), now(), 1, false);

insert into workspaces (id, tenant_id, name, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', 'Default', now(), now(), 1, false),
  ('11111111-1111-1111-1111-111111111113', '11111111-1111-1111-1111-111111111111', 'Client Delivery', now(), now(), 1, false);

insert into roles (id, tenant_id, name, is_system_role, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111121', '11111111-1111-1111-1111-111111111111', 'owner', true, now(), now(), 1, false),
  ('11111111-1111-1111-1111-111111111122', '11111111-1111-1111-1111-111111111111', 'admin', true, now(), now(), 1, false),
  ('11111111-1111-1111-1111-111111111123', '11111111-1111-1111-1111-111111111111', 'member', true, now(), now(), 1, false);

insert into users (id, email, full_name, created_at, updated_at)
values
  ('11111111-1111-1111-1111-111111111131', 'owner@acme-seed.test', 'Acme Owner', now(), now()),
  ('11111111-1111-1111-1111-111111111132', 'member@acme-seed.test', 'Acme Member', now(), now());

insert into organization_members (id, tenant_id, user_id, role_id, status, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111141', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111131', '11111111-1111-1111-1111-111111111121', 'active', now(), now(), 1, false),
  ('11111111-1111-1111-1111-111111111142', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111132', '11111111-1111-1111-1111-111111111123', 'active', now(), now(), 1, false);

-- Tenant B: Beta Consulting -- deliberately structured identically to
-- Tenant A so Sprint 3's cross-tenant tests have a same-shape "other
-- tenant" to attempt (and fail) to read across into.
insert into organizations (id, name, created_at, updated_at, version, legal_hold)
values ('22222222-2222-2222-2222-222222222221', 'Beta Consulting', now(), now(), 1, false);

insert into workspaces (id, tenant_id, name, created_at, updated_at, version, legal_hold)
values
  ('22222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222221', 'Default', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222223', '22222222-2222-2222-2222-222222222221', 'Client Delivery', now(), now(), 1, false);

insert into roles (id, tenant_id, name, is_system_role, created_at, updated_at, version, legal_hold)
values
  ('22222222-2222-2222-2222-222222222231', '22222222-2222-2222-2222-222222222221', 'owner', true, now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222232', '22222222-2222-2222-2222-222222222221', 'admin', true, now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222233', '22222222-2222-2222-2222-222222222221', 'member', true, now(), now(), 1, false);

insert into users (id, email, full_name, created_at, updated_at)
values
  ('22222222-2222-2222-2222-222222222241', 'owner@beta-seed.test', 'Beta Owner', now(), now()),
  ('22222222-2222-2222-2222-222222222242', 'member@beta-seed.test', 'Beta Member', now(), now());

insert into organization_members (id, tenant_id, user_id, role_id, status, created_at, updated_at, version, legal_hold)
values
  ('22222222-2222-2222-2222-222222222251', '22222222-2222-2222-2222-222222222221', '22222222-2222-2222-2222-222222222241', '22222222-2222-2222-2222-222222222231', 'active', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222252', '22222222-2222-2222-2222-222222222221', '22222222-2222-2222-2222-222222222242', '22222222-2222-2222-2222-222222222233', 'active', now(), now(), 1, false);

-- Global permission catalog (app.organizations.permissions_catalog.PERMISSIONS
-- is the source of truth -- this mirrors it for standalone SQL seeding, so
-- keep the two in sync if permissions change).
insert into permissions (id, key, description, created_at)
values
  ('99999999-9999-9999-9999-999999999991', 'members.invite', 'Invite new team members', now()),
  ('99999999-9999-9999-9999-999999999992', 'members.remove', 'Deactivate/remove team members', now()),
  ('99999999-9999-9999-9999-999999999993', 'members.manage_roles', 'Change a team member''s role', now()),
  ('99999999-9999-9999-9999-999999999994', 'org.manage', 'Manage organization settings', now());

insert into role_permissions (id, role_id, permission_id, created_at)
values
  -- Acme owner: all permissions
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999991', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999992', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999993', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999994', now()),
  -- Beta owner: all permissions
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999991', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999992', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999993', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999994', now());

commit;
