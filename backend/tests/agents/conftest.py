import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Reuses the same real-Supabase requirement as tests/rag/ (search_knowledge
# needs pgvector, the agent_tasks queue needs pgmq) -- one env var, one
# real project, rather than a second gate for the same underlying need.
AGENTS_DATABASE_URL = os.environ.get("RAG_TEST_DATABASE_URL")

_SKIP_REASON = (
    "RAG_TEST_DATABASE_URL not set -- these tests need a real Supabase project "
    "with the `vector` and `pgmq` extensions enabled, Sprint 1-8's Alembic "
    "migrations applied, every supabase/rls/*.sql file applied, and "
    "supabase/config/rag_queues.sql + agent_queues.sql run once as the "
    "project's admin role. See backend/tests/rag/README.md -- same "
    "requirement, reused rather than duplicated."
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """See tests/rls/conftest.py's identical hook for why a bare
    module-level `pytestmark` here would not actually skip anything."""
    if AGENTS_DATABASE_URL:
        return
    this_dir = Path(__file__).parent
    skip_marker = pytest.mark.skip(reason=_SKIP_REASON)
    for item in items:
        if this_dir in item.path.parents:
            item.add_marker(skip_marker)


@pytest_asyncio.fixture
async def pg_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(AGENTS_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
