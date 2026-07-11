ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS knowledge_chunks_select ON knowledge_chunks;
CREATE POLICY knowledge_chunks_select ON knowledge_chunks FOR SELECT
  USING (tenant_id = current_tenant_id() OR is_member_of_tenant(tenant_id));

DROP POLICY IF EXISTS knowledge_chunks_insert ON knowledge_chunks;
CREATE POLICY knowledge_chunks_insert ON knowledge_chunks FOR INSERT
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS knowledge_chunks_update ON knowledge_chunks;
CREATE POLICY knowledge_chunks_update ON knowledge_chunks FOR UPDATE
  USING (tenant_id = current_tenant_id())
  WITH CHECK (tenant_id = current_tenant_id());

DROP POLICY IF EXISTS knowledge_chunks_delete ON knowledge_chunks;
CREATE POLICY knowledge_chunks_delete ON knowledge_chunks FOR DELETE
  USING (tenant_id = current_tenant_id());
