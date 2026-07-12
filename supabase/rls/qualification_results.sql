ALTER TABLE qualification_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE qualification_results FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS qualification_results_select ON qualification_results;
CREATE POLICY qualification_results_select ON qualification_results FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS qualification_results_insert ON qualification_results;
CREATE POLICY qualification_results_insert ON qualification_results FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS qualification_results_update ON qualification_results;
CREATE POLICY qualification_results_update ON qualification_results FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS qualification_results_delete ON qualification_results;
CREATE POLICY qualification_results_delete ON qualification_results FOR DELETE
  USING (tenant_id = current_tenant_id());
