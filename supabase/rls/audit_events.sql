-- No UPDATE/DELETE policies at all -- combined with FORCE ROW LEVEL
-- SECURITY, this makes audit rows genuinely immutable through the
-- application (not just immutable by convention), per
-- docs/BDOS_Enforcement_Spec.md's audit requirements.

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS audit_events_select ON audit_events;
CREATE POLICY audit_events_select ON audit_events FOR SELECT
  USING (tenant_id = current_tenant_id());

-- Clients never write audit events directly (Flutter holds no database
-- credentials at all -- Security Invariant 1-3); this table is
-- insert-only from the backend, which always has an established tenant
-- context by the time it writes one (app/audit/writer.py is called from
-- within an already-tenant-scoped request in every current call site).
DROP POLICY IF EXISTS audit_events_insert ON audit_events;
CREATE POLICY audit_events_insert ON audit_events FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());
