-- No UPDATE/DELETE policies -- same immutable-log shape as audit_events.sql:
-- an explainability record is the permanent "why" for a decision that
-- already happened, never edited after the fact.

ALTER TABLE explainability_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE explainability_records FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS explainability_records_select ON explainability_records;
CREATE POLICY explainability_records_select ON explainability_records FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS explainability_records_insert ON explainability_records;
CREATE POLICY explainability_records_insert ON explainability_records FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());
