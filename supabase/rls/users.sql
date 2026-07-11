-- users is a global identity mirror, not tenant-scoped -- see the model
-- docstring (app/organizations/models.py) and docs/rls-pattern.md's
-- "Known exceptions" section.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- See your own profile always; see a teammate's profile only while you
-- share a tenant context with them (e.g. the team management screen).
DROP POLICY IF EXISTS users_select ON users;
CREATE POLICY users_select ON users FOR SELECT
  USING (
    id = current_actor_user_id()
    OR EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = users.id AND om.tenant_id = current_tenant_id()
    )
  );

-- You may only ever create your own profile row (get_or_create_user
-- mirrors the JWT-verified Supabase Auth identity, never someone else's).
DROP POLICY IF EXISTS users_insert ON users;
CREATE POLICY users_insert ON users FOR INSERT
  WITH CHECK (id = current_actor_user_id());

DROP POLICY IF EXISTS users_update ON users;
CREATE POLICY users_update ON users FOR UPDATE
  USING (id = current_actor_user_id())
  WITH CHECK (id = current_actor_user_id());
