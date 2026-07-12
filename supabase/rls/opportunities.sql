ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunities_select ON opportunities;
CREATE POLICY opportunities_select ON opportunities FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS opportunities_insert ON opportunities;
CREATE POLICY opportunities_insert ON opportunities FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS opportunities_update ON opportunities;
CREATE POLICY opportunities_update ON opportunities FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS opportunities_delete ON opportunities;
CREATE POLICY opportunities_delete ON opportunities FOR DELETE
  USING (tenant_id = current_tenant_id());
