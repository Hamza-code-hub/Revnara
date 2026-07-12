"""Real RLS tests (Sprint 8, DB8.1) for agent_runs/tool_actions against a
real Postgres connection (see conftest.py's skip guard if
RLS_TEST_DATABASE_URL isn't set). Same scenario shapes as
test_company_brain_isolation.py's Sprint 4 tests. Neither table needs
pgvector/pgmq, so this runs against the same "any real Postgres" tier as
the rest of tests/rls/, not the stricter tests/agents/ real-Supabase tier.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.rls.conftest import create_tenant, set_context


async def _insert_agent_run(
    session: AsyncSession, *, tenant_id: uuid.UUID, agent_id: str
) -> uuid.UUID:
    run_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO agent_runs "
            "(id, tenant_id, agent_id, agent_version, status, inputs, "
            "total_input_tokens, total_output_tokens, total_cost_usd, tool_call_count, "
            "started_at, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :agent_id, '1.0.0', 'completed', '{}', "
            "0, 0, 0, 0, now(), now(), now(), 1, false)"
        ),
        {"id": str(run_id), "tid": str(tenant_id), "agent_id": agent_id},
    )
    return run_id


async def _insert_tool_action(
    session: AsyncSession, *, tenant_id: uuid.UUID, agent_run_id: uuid.UUID, tool_name: str
) -> uuid.UUID:
    action_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO tool_actions "
            "(id, tenant_id, agent_run_id, tool_name, arguments, was_allowed, "
            "created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, :run_id, :tool_name, '{}', true, now(), now(), 1, false)"
        ),
        {
            "id": str(action_id),
            "tid": str(tenant_id),
            "run_id": str(agent_run_id),
            "tool_name": tool_name,
        },
    )
    return action_id


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_agent_runs(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Agent Co A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Agent Co B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await _insert_agent_run(pg_session, tenant_id=org_a, agent_id="agent_a")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    await _insert_agent_run(pg_session, tenant_id=org_b, agent_id="agent_b")
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT agent_id FROM agent_runs"))
    visible_agent_ids = {row[0] for row in result.all()}

    assert visible_agent_ids == {"agent_b"}


@pytest.mark.asyncio
async def test_tenant_a_cannot_insert_agent_run_claiming_tenant_b(
    pg_session: AsyncSession,
) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Agent Co A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Agent Co B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)

    with pytest.raises(DBAPIError, match="row-level security"):
        await _insert_agent_run(pg_session, tenant_id=org_a, agent_id="should_be_rejected")
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_tenant_a_cannot_select_tenant_b_tool_actions(pg_session: AsyncSession) -> None:
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Agent Co A {uuid.uuid4()}")
    org_b, _, owner_b = await create_tenant(pg_session, name=f"RLS Agent Co B {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    run_a = await _insert_agent_run(pg_session, tenant_id=org_a, agent_id="agent_a")
    await _insert_tool_action(
        pg_session, tenant_id=org_a, agent_run_id=run_a, tool_name="tool_a"
    )
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    run_b = await _insert_agent_run(pg_session, tenant_id=org_b, agent_id="agent_b")
    await _insert_tool_action(
        pg_session, tenant_id=org_b, agent_run_id=run_b, tool_name="tool_b"
    )
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_b, tenant_id=org_b)
    result = await pg_session.execute(text("SELECT tool_name FROM tool_actions"))
    visible_tool_names = {row[0] for row in result.all()}

    assert visible_tool_names == {"tool_b"}


@pytest.mark.asyncio
async def test_tool_actions_have_no_update_policy_at_all(pg_session: AsyncSession) -> None:
    """Immutable-log shape (like audit_events) -- once written, a
    tool_action can never be edited through the app role, not even by
    the tenant that owns it."""
    org_a, _, owner_a = await create_tenant(pg_session, name=f"RLS Agent Co A {uuid.uuid4()}")

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    run_a = await _insert_agent_run(pg_session, tenant_id=org_a, agent_id="agent_a")
    await _insert_tool_action(
        pg_session, tenant_id=org_a, agent_run_id=run_a, tool_name="original_tool"
    )
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    await pg_session.execute(
        text("UPDATE tool_actions SET tool_name = 'tampered' WHERE agent_run_id = :run_id"),
        {"run_id": str(run_a)},
    )
    await pg_session.commit()

    await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
    result = await pg_session.execute(
        text("SELECT tool_name FROM tool_actions WHERE agent_run_id = :run_id"),
        {"run_id": str(run_a)},
    )
    assert result.scalar_one() == "original_tool"
