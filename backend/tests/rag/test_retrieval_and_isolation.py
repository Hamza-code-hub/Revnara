"""Real pgvector similarity search tests (BE5.3, Blueprint §57 AV-002)
against a real Supabase project -- see conftest.py's skip guard.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.models import EMBEDDING_DIMENSIONS, KnowledgeChunk
from app.rag.retrieval import search
from tests.rag.conftest import cleanup_tenant, create_tenant, set_context

_QUERY_VECTOR = [1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1)
_CLOSE_VECTOR = [0.99] + [0.0] * (EMBEDDING_DIMENSIONS - 1)
_FAR_VECTOR = [-1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1)


async def _insert_chunk(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    tenant_id: uuid.UUID,
    text: str,
    embedding: list[float],
    classification: str | None = None,
) -> None:
    # set_config's third argument (true = transaction-local) means context
    # resets the moment any previous commit ends that transaction -- set it
    # again immediately before every commit-ending operation rather than
    # once per test "phase" (the exact bug this project has already hit
    # twice before: Sprint 4's test_company_brain_isolation.py, and this
    # file's own first draft, which failed with a real RLS rejection on
    # the *second* insert in a tenant, not the first).
    await set_context(session, user_id=owner_id, tenant_id=tenant_id)
    session.add(
        KnowledgeChunk(
            tenant_id=tenant_id,
            source_type="portfolio_item",
            source_id=uuid.uuid4(),
            chunk_index=0,
            chunk_text=text,
            embedding=embedding,
            classification=classification,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_search_orders_by_similarity_and_stays_within_tenant(
    pg_session: AsyncSession,
) -> None:
    org_a, owner_a = await create_tenant(pg_session, name=f"RAG Test A {uuid.uuid4()}")
    org_b, owner_b = await create_tenant(pg_session, name=f"RAG Test B {uuid.uuid4()}")

    try:
        await _insert_chunk(
            pg_session,
            owner_id=owner_a,
            tenant_id=org_a,
            text="close match",
            embedding=_CLOSE_VECTOR,
        )
        await _insert_chunk(
            pg_session, owner_id=owner_a, tenant_id=org_a, text="far match", embedding=_FAR_VECTOR
        )
        await _insert_chunk(
            pg_session,
            owner_id=owner_b,
            tenant_id=org_b,
            text="tenant b's own close match",
            embedding=_CLOSE_VECTOR,
        )

        await set_context(pg_session, user_id=owner_a, tenant_id=org_a)
        results = await search(
            pg_session,
            query_embedding=_QUERY_VECTOR,
            tenant_id=org_a,
            actor_permissions=frozenset(),
            limit=10,
        )

        texts = [r.chunk_text for r in results]
        assert texts == ["close match", "far match"], (
            "expected closest match first, tenant b excluded"
        )
        assert results[0].distance < results[1].distance
    finally:
        await cleanup_tenant(pg_session, org_id=org_a, owner_user_id=owner_a)
        await cleanup_tenant(pg_session, org_id=org_b, owner_user_id=owner_b)


@pytest.mark.asyncio
async def test_confidential_chunks_require_company_manage_permission(
    pg_session: AsyncSession,
) -> None:
    org_id, owner_id = await create_tenant(
        pg_session, name=f"RAG Test Confidential {uuid.uuid4()}"
    )

    try:
        await _insert_chunk(
            pg_session,
            owner_id=owner_id,
            tenant_id=org_id,
            text="public info",
            embedding=_CLOSE_VECTOR,
        )
        await _insert_chunk(
            pg_session,
            owner_id=owner_id,
            tenant_id=org_id,
            text="confidential info",
            embedding=_CLOSE_VECTOR,
            classification="confidential",
        )

        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        without_permission = await search(
            pg_session,
            query_embedding=_QUERY_VECTOR,
            tenant_id=org_id,
            actor_permissions=frozenset(),
            limit=10,
        )
        assert {r.chunk_text for r in without_permission} == {"public info"}

        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        with_permission = await search(
            pg_session,
            query_embedding=_QUERY_VECTOR,
            tenant_id=org_id,
            actor_permissions=frozenset({"company.manage"}),
            limit=10,
        )
        assert {r.chunk_text for r in with_permission} == {"public info", "confidential info"}
    finally:
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)


@pytest.mark.asyncio
async def test_unclassified_chunks_are_always_visible_regardless_of_permission(
    pg_session: AsyncSession,
) -> None:
    """Regression guard for the NULL-classification bug caught while
    writing retrieval.py: a plain `classification != 'confidential'`
    filter would have also excluded NULL-classification rows (SQL's
    three-valued NULL comparison logic), which is why retrieval.py uses
    `IS DISTINCT FROM` instead -- this test would fail if that regressed
    back to a plain `!=`."""
    org_id, owner_id = await create_tenant(pg_session, name=f"RAG Test Null {uuid.uuid4()}")

    try:
        await _insert_chunk(
            pg_session,
            owner_id=owner_id,
            tenant_id=org_id,
            text="unclassified",
            embedding=_CLOSE_VECTOR,
        )

        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        results = await search(
            pg_session,
            query_embedding=_QUERY_VECTOR,
            tenant_id=org_id,
            actor_permissions=frozenset(),
            limit=10,
        )
        assert {r.chunk_text for r in results} == {"unclassified"}
    finally:
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)


@pytest.mark.asyncio
async def test_search_respects_limit(pg_session: AsyncSession) -> None:
    org_id, owner_id = await create_tenant(pg_session, name=f"RAG Test Limit {uuid.uuid4()}")

    try:
        for i in range(5):
            await _insert_chunk(
                pg_session,
                owner_id=owner_id,
                tenant_id=org_id,
                text=f"chunk {i}",
                embedding=_CLOSE_VECTOR,
            )

        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        results = await search(
            pg_session,
            query_embedding=_QUERY_VECTOR,
            tenant_id=org_id,
            actor_permissions=frozenset(),
            limit=2,
        )
        assert len(results) == 2
    finally:
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)
