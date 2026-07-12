-- No UPDATE/DELETE policies -- same immutable-log shape as audit_events.sql:
-- an override record is a permanent capture of a human's correction,
-- never edited or deleted after the fact (it's the data source Sprint
-- 25's win/loss learning loop depends on).

ALTER TABLE override_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE override_records FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS override_records_select ON override_records;
CREATE POLICY override_records_select ON override_records FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS override_records_insert ON override_records;
CREATE POLICY override_records_insert ON override_records FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());
