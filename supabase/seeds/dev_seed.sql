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
  ('99999999-9999-9999-9999-999999999994', 'org.manage', 'Manage organization settings', now()),
  ('99999999-9999-9999-9999-999999999995', 'company.manage', 'Manage company profile, team, skills, and portfolio', now());

insert into role_permissions (id, role_id, permission_id, created_at)
values
  -- Acme owner: all permissions
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999991', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999992', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999993', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999994', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111121', '99999999-9999-9999-9999-999999999995', now()),
  -- Beta owner: all permissions
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999991', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999992', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999993', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999994', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222231', '99999999-9999-9999-9999-999999999995', now());

-- Sprint 4 (Company Brain, DB4.3): company profile fields + team/skills/
-- portfolio/case-study sample data for both dev tenants.

update organizations set
  description = 'Acme Software builds custom web and mobile products for mid-market clients.',
  industry = 'Software Consulting',
  website = 'https://acme-seed.test',
  founded_year = 2015
where id = '11111111-1111-1111-1111-111111111111';

update organizations set
  description = 'Beta Consulting delivers data platform and analytics engagements.',
  industry = 'Data & Analytics Consulting',
  website = 'https://beta-seed.test',
  founded_year = 2018
where id = '22222222-2222-2222-2222-222222222221';

insert into skills (id, tenant_id, name, category, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111151', '11111111-1111-1111-1111-111111111111', 'Flutter', 'Frontend', now(), now(), 1, false),
  ('11111111-1111-1111-1111-111111111152', '11111111-1111-1111-1111-111111111111', 'FastAPI', 'Backend', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222261', '22222222-2222-2222-2222-222222222221', 'PostgreSQL', 'Data', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222262', '22222222-2222-2222-2222-222222222221', 'dbt', 'Data', now(), now(), 1, false);

insert into team_members (id, tenant_id, name, title, email, bio, hourly_rate, currency, weekly_availability_hours, is_active, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111161', '11111111-1111-1111-1111-111111111111', 'Alex Rivera', 'Lead Engineer', 'alex@acme-seed.test', 'Full-stack lead with 8 years of Flutter/FastAPI delivery.', 95.00, 'USD', 30, true, now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222271', '22222222-2222-2222-2222-222222222221', 'Jordan Lee', 'Data Engineer', 'jordan@beta-seed.test', 'Analytics engineer specializing in warehouse modeling.', 85.00, 'USD', 25, true, now(), now(), 1, false);

insert into team_member_skills (id, team_member_id, skill_id, proficiency_level, created_at)
values
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111161', '11111111-1111-1111-1111-111111111151', 'expert', now()),
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111161', '11111111-1111-1111-1111-111111111152', 'expert', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222271', '22222222-2222-2222-2222-222222222261', 'expert', now()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222271', '22222222-2222-2222-2222-222222222262', 'intermediate', now());

insert into portfolio_items (id, tenant_id, title, description, client_name, technologies, project_url, completed_at, classification, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111171', '11111111-1111-1111-1111-111111111111', 'Inventory Management Rebuild', 'Rebuilt a legacy inventory system as a Flutter + FastAPI app.', 'Acme Retail Client', 'Flutter, FastAPI, PostgreSQL', 'https://acme-seed.test/case/inventory', '2025-11-01 00:00:00+00', 'public', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222281', '22222222-2222-2222-2222-222222222221', 'Sales Analytics Warehouse', 'Stood up a dbt-based analytics warehouse and dashboard suite.', 'Beta Retail Client', 'PostgreSQL, dbt', 'https://beta-seed.test/case/warehouse', '2025-09-15 00:00:00+00', 'confidential', now(), now(), 1, false);

insert into case_studies (id, tenant_id, portfolio_item_id, title, summary, content, outcome_metrics, classification, created_at, updated_at, version, legal_hold)
values
  ('11111111-1111-1111-1111-111111111181', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111171', 'How Acme Cut Inventory Errors by 40%', 'A rebuild of a client''s inventory system.', 'Full narrative of the engagement, approach, and delivery timeline.', 'Inventory discrepancies down 40%, page load time down 60%.', 'public', now(), now(), 1, false),
  ('22222222-2222-2222-2222-222222222291', '22222222-2222-2222-2222-222222222221', '22222222-2222-2222-2222-222222222281', 'Beta''s Analytics Warehouse Rollout', 'Confidential engagement summary -- internal use only.', 'Full narrative restricted to internal reference; not for external proposal citation.', 'Query latency down 70%.', 'confidential', now(), now(), 1, false);

commit;
