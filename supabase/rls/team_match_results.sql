ALTER TABLE team_match_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_match_results FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS team_match_results_select ON team_match_results;
CREATE POLICY team_match_results_select ON team_match_results FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS team_match_results_insert ON team_match_results;
CREATE POLICY team_match_results_insert ON team_match_results FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS team_match_results_update ON team_match_results;
CREATE POLICY team_match_results_update ON team_match_results FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS team_match_results_delete ON team_match_results;
CREATE POLICY team_match_results_delete ON team_match_results FOR DELETE
  USING (tenant_id = current_tenant_id());
