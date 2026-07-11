-- The SELECT policy's `user_id = current_actor_user_id()` clause is
-- load-bearing beyond just "see your own row": it's what lets
-- GET /me list every organization a user belongs to without a single
-- current tenant set, AND it's what lets is_member_of_tenant() (used by
-- every other table's policies) query this table without recursing into
-- a table it can't yet see. See docs/rls-pattern.md.

ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS organization_members_select ON organization_members;
CREATE POLICY organization_members_select ON organization_members FOR SELECT
  USING (tenant_id = current_tenant_id() OR user_id = current_actor_user_id());

-- Mutations require the current, established tenant context -- unlike
-- SELECT, there is no "or it's my own row" fallback for insert/update/
-- delete: inviting/promoting/deactivating a member is always an action
-- taken *within* a tenant, including the owner-membership row created
-- during org-creation bootstrap (which sets current_tenant_id right
-- before this insert -- see organizations/service.py).
DROP POLICY IF EXISTS organization_members_insert ON organization_members;
CREATE POLICY organization_members_insert ON organization_members FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS organization_members_update ON organization_members;
CREATE POLICY organization_members_update ON organization_members FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS organization_members_delete ON organization_members;
CREATE POLICY organization_members_delete ON organization_members FOR DELETE
  USING (tenant_id = current_tenant_id());
