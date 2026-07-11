"""Real RLS tests against a real Postgres connection (see conftest.py's
skip guard if RLS_TEST_DATABASE_URL isn't set). These are the automated,
repeatable form of the manual verification performed while building
Sprint 3 -- every scenario here was proven by hand against a local
portable Postgres before being written down as a permanent test.

Per docs/BDOS_Enterprise_Architecture_Blueprint_v2_Validated.md §25's
Mandatory Test: "No user, agent, service, tool, retrieval query, export,
or support function may access another tenant's data without an explicit
audited administrative process."
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.rls.conftest import create_tenant, set_context


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_workspace_via_direct_filter(
    pg_session: AsyncSession,
) -> None:
    org_a, ws_a, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, ws_b, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)

    # Own workspace: visible.
    own = await pg_session.execute(
        text("SELECT id FROM workspaces WHERE tenant_id = :tid"), {"tid": str(org_b)}
    )
    assert own.scalar_one() == ws_b

    # Explicitly filtering for Tenant A's workspace while in Tenant B's
    # context returns zero rows -- RLS silently filters it out even
    # though the WHERE clause asked for exactly that tenant_id.
    other = await pg_session.execute(
        text("SELECT id FROM workspaces WHERE tenant_id = :tid"), {"tid": str(org_a)}
    )
    assert other.first() is None


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_workspace_with_no_where_clause(
    pg_session: AsyncSession,
) -> None:
    """The stronger version of the test above: no WHERE clause at all
    still only returns the current tenant's own row(s)."""
    org_a, ws_a, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, ws_b, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)

    result = await pg_session.execute(text("SELECT tenant_id FROM workspaces"))
    visible_tenant_ids = {row[0] for row in result.all()}

    assert org_b in visible_tenant_ids
    assert org_a not in visible_tenant_ids


@pytest.mark.asyncio
async def test_tenant_a_cannot_update_tenant_b_row(pg_session: AsyncSession) -> None:
    org_a, ws_a, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, ws_b, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(
        text("UPDATE workspaces SET name = 'HACKED' WHERE tenant_id = :tid"),
        {"tid": str(org_a)},
    )
    assert result.rowcount == 0
    await pg_session.commit()

    # Confirm from Tenant A's own context that its row is untouched.
    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    check = await pg_session.execute(
        text("SELECT name FROM workspaces WHERE tenant_id = :tid"), {"tid": str(org_a)}
    )
    assert check.scalar_one() == "Default"


@pytest.mark.asyncio
async def test_tenant_a_cannot_delete_tenant_b_organization(pg_session: AsyncSession) -> None:
    org_a, ws_a, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, ws_b, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(
        text("DELETE FROM organizations WHERE id = :id"), {"id": str(org_a)}
    )
    assert result.rowcount == 0
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    check = await pg_session.execute(
        text("SELECT id FROM organizations WHERE id = :id"), {"id": str(org_a)}
    )
    assert check.scalar_one() == org_a


@pytest.mark.asyncio
async def test_anonymous_no_context_query_returns_zero_rows(pg_session: AsyncSession) -> None:
    """A fresh session/transaction with neither app.current_user_id nor
    app.current_tenant_id ever set must see nothing on tenant-scoped
    tables -- unset session state fails closed, not open."""
    await create_tenant(pg_session, name=f"RLS Test Anon {uuid.uuid4()}")

    # Deliberately no set_context call in this test.
    orgs = await pg_session.execute(text("SELECT count(*) FROM organizations"))
    assert orgs.scalar_one() == 0

    workspaces = await pg_session.execute(text("SELECT count(*) FROM workspaces"))
    assert workspaces.scalar_one() == 0

    members = await pg_session.execute(text("SELECT count(*) FROM organization_members"))
    assert members.scalar_one() == 0


@pytest.mark.asyncio
async def test_audit_event_insert_with_mismatched_tenant_id_is_rejected(
    pg_session: AsyncSession,
) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    # In Tenant B's context, attempt to insert an audit event claiming
    # Tenant A's tenant_id -- the INSERT's WITH CHECK must reject this
    # outright (a hard error, not a silent no-op, since INSERT policies
    # behave differently from SELECT/UPDATE/DELETE's silent filtering).
    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)

    with pytest.raises(DBAPIError, match="row-level security"):
        await pg_session.execute(
            text(
                "INSERT INTO audit_events "
                "(id, tenant_id, actor_type, actor_id, action_type, outcome, created_at) "
                "VALUES (:id, :tenant_id, 'user', :actor_id, 'test.mismatch', 'executed', now())"
            ),
            {"id": str(uuid.uuid4()), "tenant_id": str(org_a), "actor_id": str(owner_b)},
        )
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_users_table_shows_own_row_and_tenant_teammates_only(
    pg_session: AsyncSession,
) -> None:
    """users is a global identity mirror, not tenant-scoped -- confirms
    the "see yourself always, see a teammate only within a shared tenant
    context" policy from supabase/rls/users.sql. create_tenant already
    creates each owner's `users` row (it has to, for the FK on
    organization_members.user_id) -- no need to insert it again here."""
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Test A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Test B {uuid.uuid4()}")

    # In Tenant A's context: see own row and Tenant A teammates, not
    # Tenant B's owner.
    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    result = await pg_session.execute(text("SELECT id FROM users"))
    visible = {row[0] for row in result.all()}

    assert owner_a in visible
    assert owner_b not in visible
