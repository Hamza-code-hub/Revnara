ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS skills_select ON skills;
CREATE POLICY skills_select ON skills FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS skills_insert ON skills;
CREATE POLICY skills_insert ON skills FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS skills_update ON skills;
CREATE POLICY skills_update ON skills FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS skills_delete ON skills;
CREATE POLICY skills_delete ON skills FOR DELETE
  USING (tenant_id = current_tenant_id());
