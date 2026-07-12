-- No UPDATE policy -- a tool-call attempt (allowed or blocked) is
-- written once by the executor and never edited afterward, same
-- tamper-proof intent as audit_events.sql. DELETE *is* permitted
-- (unlike audit_events), tenant-scoped like any other business table --
-- tool_actions is a child row of agent_runs (FK, no ON DELETE CASCADE),
-- so agent_runs.sql's own DELETE policy would otherwise be blocked
-- forever by this table's rows referencing it (confirmed for real: a
-- test cleanup attempt hit exactly this FK-violation deadlock before
-- this policy existed).

ALTER TABLE tool_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_actions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tool_actions_select ON tool_actions;
CREATE POLICY tool_actions_select ON tool_actions FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS tool_actions_insert ON tool_actions;
CREATE POLICY tool_actions_insert ON tool_actions FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS tool_actions_delete ON tool_actions;
CREATE POLICY tool_actions_delete ON tool_actions FOR DELETE
  USING (tenant_id = current_tenant_id());
