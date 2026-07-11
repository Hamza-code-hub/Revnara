-- Helper functions used by every policy file in this directory.
-- See docs/rls-pattern.md before changing anything here -- these three
-- functions are the entire trust boundary every other policy relies on.

CREATE OR REPLACE FUNCTION current_actor_user_id() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
$$ LANGUAGE sql STABLE;

-- Deliberately NOT SECURITY DEFINER: this only ever checks for a
-- membership row belonging to current_actor_user_id() themselves, and
-- organization_members.sql's own SELECT policy already allows a user to
-- see their own membership rows unconditionally (regardless of current
-- tenant) -- so this works correctly under the caller's own RLS context
-- without needing to bypass it. If this function is ever changed to
-- check a *different* user's membership, that assumption breaks and
-- SECURITY DEFINER would need real scrutiny, not casual addition.
CREATE OR REPLACE FUNCTION is_member_of_tenant(check_tenant_id uuid) RETURNS boolean AS $$
  SELECT EXISTS (
    SELECT 1 FROM organization_members om
    WHERE om.tenant_id = check_tenant_id AND om.user_id = current_actor_user_id()
  )
$$ LANGUAGE sql STABLE;
