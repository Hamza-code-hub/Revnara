ALTER TABLE portfolio_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_items FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS portfolio_items_select ON portfolio_items;
CREATE POLICY portfolio_items_select ON portfolio_items FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS portfolio_items_insert ON portfolio_items;
CREATE POLICY portfolio_items_insert ON portfolio_items FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS portfolio_items_update ON portfolio_items;
CREATE POLICY portfolio_items_update ON portfolio_items FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS portfolio_items_delete ON portfolio_items;
CREATE POLICY portfolio_items_delete ON portfolio_items FOR DELETE
  USING (tenant_id = current_tenant_id());
