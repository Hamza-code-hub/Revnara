ALTER TABLE case_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_studies FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS case_studies_select ON case_studies;
CREATE POLICY case_studies_select ON case_studies FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS case_studies_insert ON case_studies;
CREATE POLICY case_studies_insert ON case_studies FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS case_studies_update ON case_studies;
CREATE POLICY case_studies_update ON case_studies FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS case_studies_delete ON case_studies;
CREATE POLICY case_studies_delete ON case_studies FOR DELETE
  USING (tenant_id = current_tenant_id());
