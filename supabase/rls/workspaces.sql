ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS workspaces_select ON workspaces;
CREATE POLICY workspaces_select ON workspaces FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS workspaces_insert ON workspaces;
CREATE POLICY workspaces_insert ON workspaces FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS workspaces_update ON workspaces;
CREATE POLICY workspaces_update ON workspaces FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS workspaces_delete ON workspaces;
CREATE POLICY workspaces_delete ON workspaces FOR DELETE
  USING (tenant_id = current_tenant_id());
