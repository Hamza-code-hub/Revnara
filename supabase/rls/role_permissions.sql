-- role_permissions is a pure join table with no tenant_id of its own --
-- policies reach through to the associated role's tenant_id.

ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS role_permissions_select ON role_permissions;
CREATE POLICY role_permissions_select ON role_permissions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM roles r
      WHERE r.id = role_permissions.role_id
        AND (r.tenant_id = current_tenant_id() OR is_member_of_tenant(r.tenant_id))
    )
  );

DROP POLICY IF EXISTS role_permissions_insert ON role_permissions;
CREATE POLICY role_permissions_insert ON role_permissions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM roles r
      WHERE r.id = role_permissions.role_id AND r.tenant_id = current_tenant_id()
    )
  );

DROP POLICY IF EXISTS role_permissions_delete ON role_permissions;
CREATE POLICY role_permissions_delete ON role_permissions FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM roles r
      WHERE r.id = role_permissions.role_id AND r.tenant_id = current_tenant_id()
    )
  );
