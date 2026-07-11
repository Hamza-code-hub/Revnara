import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

RAG_DATABASE_URL = os.environ.get("RAG_TEST_DATABASE_URL")

_SKIP_REASON = (
    "RAG_TEST_DATABASE_URL not set -- these tests need a real Supabase project "
    "with the `vector` and `pgmq` extensions enabled (confirmed empirically not "
    "available on a vanilla local Postgres install, see docs/rag-pattern.md), "
    "Sprint 1-5's Alembic migrations applied, every supabase/rls/*.sql file "
    "applied, and supabase/config/rag_queues.sql run once as the project's "
    "admin role. See backend/tests/rag/README.md."
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """See tests/rls/conftest.py's identical hook for why a bare
    module-level `pytestmark` here would not actually skip anything."""
    if RAG_DATABASE_URL:
        return
    this_dir = Path(__file__).parent
    skip_marker = pytest.mark.skip(reason=_SKIP_REASON)
    for item in items:
        if this_dir in item.path.parents:
            item.add_marker(skip_marker)


@pytest_asyncio.fixture
async def pg_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(RAG_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def set_context(
    session: AsyncSession, *, user_id: uuid.UUID, tenant_id: uuid.UUID | None = None
) -> None:
    """Same mechanism as backend/tests/rls/conftest.py's helper of the same
    name -- mirrors app/tenancy/pg_session.py exactly."""
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(user_id)}
    )
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)}
        )


async def create_tenant(session: AsyncSession, *, name: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Minimal tenant bootstrap for RAG tests -- only what knowledge_chunks'
    RLS policy needs (an organization + an active owner membership), not
    the full workspace/roles/permissions bootstrap
    backend/tests/rls/conftest.py's version does, since these tests don't
    exercise authorization. Returns (organization_id, owner_user_id).
    """
    owner_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    role_id = uuid.uuid4()
    member_id = uuid.uuid4()

    await set_context(session, user_id=owner_user_id)
    await session.execute(
        text(
            "INSERT INTO users (id, email, created_at, updated_at) "
            "VALUES (:id, :email, now(), now())"
        ),
        {"id": str(owner_user_id), "email": f"{owner_user_id}@rag-test.example"},
    )
    await session.execute(
        text(
            "INSERT INTO organizations (id, name, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :name, now(), now(), 1, false)"
        ),
        {"id": str(org_id), "name": name},
    )

    await set_context(session, user_id=owner_user_id, tenant_id=org_id)
    await session.execute(
        text(
            "INSERT INTO roles "
            "(id, tenant_id, name, is_system_role, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, 'owner', true, now(), now(), 1, false)"
        ),
        {"id": str(role_id), "tid": str(org_id)},
    )
    await session.execute(
        text(
            "INSERT INTO organization_members "
            "(id, tenant_id, user_id, role_id, status, created_at, updated_at, version, "
            "legal_hold) "
            "VALUES (:id, :tid, :uid, :rid, 'active', now(), now(), 1, false)"
        ),
        {"id": str(member_id), "tid": str(org_id), "uid": str(owner_user_id), "rid": str(role_id)},
    )
    await session.commit()

    return org_id, owner_user_id


async def cleanup_tenant(
    session: AsyncSession, *, org_id: uuid.UUID, owner_user_id: uuid.UUID
) -> None:
    await set_context(session, user_id=owner_user_id, tenant_id=org_id)
    await session.execute(
        text("DELETE FROM knowledge_chunks WHERE tenant_id = :tid"), {"tid": str(org_id)}
    )
    await session.execute(
        text("DELETE FROM organization_members WHERE tenant_id = :tid"), {"tid": str(org_id)}
    )
    await session.execute(text("DELETE FROM roles WHERE tenant_id = :tid"), {"tid": str(org_id)})
    await session.execute(
        text("DELETE FROM organizations WHERE id = :id"), {"id": str(org_id)}
    )
    await session.commit()
