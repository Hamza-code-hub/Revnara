-- permissions is a global, code-defined catalog (app/organizations/
-- permissions_catalog.py), not tenant data -- see docs/rls-pattern.md's
-- "Known exceptions" section. RLS is enabled (so this table is never
-- silently missed by the CI check that looks for tables without RLS at
-- all, DQ3.1) but deliberately NOT forced: migrations/seeds running as
-- the table owner need to freely manage this catalog, and there is no
-- tenant-identifying data here for a non-owner role to be protected from.

ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS permissions_select ON permissions;
CREATE POLICY permissions_select ON permissions FOR SELECT
  USING (true);
