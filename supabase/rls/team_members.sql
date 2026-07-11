ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS team_members_select ON team_members;
CREATE POLICY team_members_select ON team_members FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS team_members_insert ON team_members;
CREATE POLICY team_members_insert ON team_members FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS team_members_update ON team_members;
CREATE POLICY team_members_update ON team_members FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS team_members_delete ON team_members;
CREATE POLICY team_members_delete ON team_members FOR DELETE
  USING (tenant_id = current_tenant_id());
