-- team_member_skills is a pure join table with no tenant_id of its own --
-- policies reach through to the associated team member's tenant_id, same
-- pattern as role_permissions.sql.

ALTER TABLE team_member_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_member_skills FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS team_member_skills_select ON team_member_skills;
CREATE POLICY team_member_skills_select ON team_member_skills FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM team_members tm
      WHERE tm.id = team_member_skills.team_member_id
        AND (tm.tenant_id = current_tenant_id() OR is_member_of_tenant(tm.tenant_id))
    )
  );

DROP POLICY IF EXISTS team_member_skills_insert ON team_member_skills;
CREATE POLICY team_member_skills_insert ON team_member_skills FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM team_members tm
      WHERE tm.id = team_member_skills.team_member_id AND tm.tenant_id = current_tenant_id()
    )
  );

DROP POLICY IF EXISTS team_member_skills_delete ON team_member_skills;
CREATE POLICY team_member_skills_delete ON team_member_skills FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM team_members tm
      WHERE tm.id = team_member_skills.team_member_id AND tm.tenant_id = current_tenant_id()
    )
  );
