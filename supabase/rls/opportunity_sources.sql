ALTER TABLE opportunity_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunity_sources FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_sources_select ON opportunity_sources;
CREATE POLICY opportunity_sources_select ON opportunity_sources FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS opportunity_sources_insert ON opportunity_sources;
CREATE POLICY opportunity_sources_insert ON opportunity_sources FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS opportunity_sources_update ON opportunity_sources;
CREATE POLICY opportunity_sources_update ON opportunity_sources FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS opportunity_sources_delete ON opportunity_sources;
CREATE POLICY opportunity_sources_delete ON opportunity_sources FOR DELETE
  USING (tenant_id = current_tenant_id());
