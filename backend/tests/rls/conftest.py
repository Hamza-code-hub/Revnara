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

RLS_DATABASE_URL = os.environ.get("RLS_TEST_DATABASE_URL")

_SKIP_REASON = (
    "RLS_TEST_DATABASE_URL not set -- these tests require a real Postgres "
    "connection, with Sprint 1-3's Alembic migrations and every "
    "supabase/rls/*.sql file already applied, connected as a NON-superuser "
    "role (superusers bypass RLS/FORCE RLS entirely, which would make "
    "these tests pass for the wrong reason). SQLite has no RLS at all. "
    "See docs/rls-pattern.md and backend/tests/rls/README.md."
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """A bare module-level `pytestmark` in a conftest.py does NOT apply to
    sibling test modules in the same directory -- confirmed by actually
    running `pytest tests/rls` with the env var unset and getting a wall
    of connection errors instead of clean skips, not assumed from how
    `pytestmark` behaves when placed directly in a test file. This hook
    is the correct, directory-scoped way to do it, filtered to only this
    conftest's own directory since `pytest_collection_modifyitems` runs
    against the whole session's collected items, not just local ones.
    """
    if RLS_DATABASE_URL:
        return
    this_dir = Path(__file__).parent
    skip_marker = pytest.mark.skip(reason=_SKIP_REASON)
    for item in items:
        if this_dir in item.path.parents:
            item.add_marker(skip_marker)


@pytest_asyncio.fixture
async def pg_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(RLS_DATABASE_URL)
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
    """Mirrors app/tenancy/pg_session.py exactly -- these tests exercise the
    same session-variable mechanism the real app uses, not a test-only
    shortcut, so a bug in the real mechanism shows up here too."""
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(user_id)}
    )
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)}
        )


async def create_tenant(
    session: AsyncSession, *, name: str
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Creates an organization + default workspace + owner role + active
    owner membership directly via SQL (bypassing the API/service layer --
    this module's job is testing the database layer in isolation), using
    the same actor-then-tenant SET LOCAL ordering the real app uses (see
    docs/rls-pattern.md's "Bootstrap ordering"). Commits internally (a
    fresh transaction is needed to change SET LOCAL context partway
    through), so test data is NOT rolled back automatically -- each test
    uses fresh random UUIDs specifically so leftover data from previous
    runs never interferes with assertions. See tests/rls/README.md.

    Returns (organization_id, workspace_id, owner_user_id).
    """
    owner_user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    role_id = uuid.uuid4()
    member_id = uuid.uuid4()

    await set_context(session, user_id=owner_user_id)
    # organization_members.user_id has a real FK to users.id (BE3.5 --
    # tenant_id is a real FK too, see app/db_mixins.py) -- this row must
    # exist before the membership insert below, mirroring get_or_create_user
    # being called before create_organization in the real request flow
    # (app/organizations/router.py).
    await session.execute(
        text(
            "INSERT INTO users (id, email, created_at, updated_at) "
            "VALUES (:id, :email, now(), now())"
        ),
        {"id": str(owner_user_id), "email": f"{owner_user_id}@rls-test.example"},
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
            "INSERT INTO workspaces "
            "(id, tenant_id, name, created_at, updated_at, version, legal_hold) "
            "VALUES (:id, :tid, 'Default', now(), now(), 1, false)"
        ),
        {"id": str(workspace_id), "tid": str(org_id)},
    )
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
        {
            "id": str(member_id),
            "tid": str(org_id),
            "uid": str(owner_user_id),
            "rid": str(role_id),
        },
    )
    await session.commit()

    return org_id, workspace_id, owner_user_id
