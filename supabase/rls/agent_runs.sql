-- No UPDATE/DELETE-by-others policy beyond the owning tenant's own
-- writes -- agent_runs IS updated in place by the same request/worker
-- that created it (status/outputs/cost accumulate across the run), so
-- unlike audit_events.sql this table does need an UPDATE policy, just
-- still tenant-scoped like everything else.

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS agent_runs_select ON agent_runs;
CREATE POLICY agent_runs_select ON agent_runs FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS agent_runs_insert ON agent_runs;
CREATE POLICY agent_runs_insert ON agent_runs FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS agent_runs_update ON agent_runs;
CREATE POLICY agent_runs_update ON agent_runs FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS agent_runs_delete ON agent_runs;
CREATE POLICY agent_runs_delete ON agent_runs FOR DELETE
  USING (tenant_id = current_tenant_id());
