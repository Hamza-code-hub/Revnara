ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE files FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS files_select ON files;
CREATE POLICY files_select ON files FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS files_insert ON files;
CREATE POLICY files_insert ON files FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS files_update ON files;
CREATE POLICY files_update ON files FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS files_delete ON files;
CREATE POLICY files_delete ON files FOR DELETE
  USING (tenant_id = current_tenant_id());
