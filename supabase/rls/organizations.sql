-- organizations IS the tenant -- no tenant_id column, policies use `id`
-- directly. See docs/rls-pattern.md's "Known exceptions" section.

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS organizations_select ON organizations;
CREATE POLICY organizations_select ON organizations FOR SELECT
  USING (id = current_tenant_id() OR is_member_of_tenant(id));

-- Creating a new organization never requires already belonging to one --
-- and at the moment of insert, current_tenant_id() cannot be set yet
-- anyway (the row has no id until after this insert). See
-- docs/rls-pattern.md's "Bootstrap ordering" section.
DROP POLICY IF EXISTS organizations_insert ON organizations;
CREATE POLICY organizations_insert ON organizations FOR INSERT
  WITH CHECK (true);

DROP POLICY IF EXISTS organizations_update ON organizations;
CREATE POLICY organizations_update ON organizations FOR UPDATE
  USING (id = current_tenant_id())
  WITH CHECK (id = current_tenant_id());

DROP POLICY IF EXISTS organizations_delete ON organizations;
CREATE POLICY organizations_delete ON organizations FOR DELETE
  USING (id = current_tenant_id());
