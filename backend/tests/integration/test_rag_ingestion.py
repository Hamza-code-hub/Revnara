import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizations.models import Organization
from app.rag import queue
from app.rag.ingestion import delete_chunks_for_source, enqueue_embedding_tasks
from app.rag.models import EMBEDDING_DIMENSIONS, KnowledgeChunk


async def _make_organization(db: AsyncSession) -> uuid.UUID:
    org = Organization(name="Ingestion Test Org")
    db.add(org)
    await db.flush()
    return org.id


@pytest.mark.asyncio
async def test_enqueue_embedding_tasks_sends_one_message_per_chunk(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_id = await _make_organization(db_session)
    source_id = uuid.uuid4()

    sent_payloads: list[dict[str, object]] = []

    async def fake_send(db: AsyncSession, queue_name: str, payload: dict[str, object]) -> int:
        assert queue_name == "embedding_tasks"
        sent_payloads.append(payload)
        return len(sent_payloads)

    monkeypatch.setattr(queue, "send", fake_send)

    # Long enough to produce more than one chunk at the default chunk_size.
    text = " ".join(f"word{i}" for i in range(400))
    chunk_count = await enqueue_embedding_tasks(
        db_session,
        tenant_id=tenant_id,
        workspace_id=None,
        source_type="portfolio_item",
        source_id=source_id,
        text=text,
        classification="public",
        source_version=1,
    )

    assert chunk_count > 1
    assert len(sent_payloads) == chunk_count

    for index, payload in enumerate(sent_payloads):
        assert payload["source_type"] == "portfolio_item"
        assert payload["resource_id"] == str(source_id)
        assert payload["chunk_index"] == index
        assert payload["idempotency_key"] == f"{source_id}:{index}:v1"
        assert payload["classification"] == "public"


@pytest.mark.asyncio
async def test_enqueue_embedding_tasks_with_empty_text_sends_nothing(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_id = await _make_organization(db_session)
    calls = []
    monkeypatch.setattr(
        queue, "send", lambda db, name, payload: calls.append(payload) or 0  # type: ignore[func-returns-value]
    )

    chunk_count = await enqueue_embedding_tasks(
        db_session,
        tenant_id=tenant_id,
        workspace_id=None,
        source_type="portfolio_item",
        source_id=uuid.uuid4(),
        text="   ",
        classification=None,
    )

    assert chunk_count == 0
    assert calls == []


@pytest.mark.asyncio
async def test_delete_chunks_for_source_removes_only_matching_rows(
    db_session: AsyncSession,
) -> None:
    tenant_id = await _make_organization(db_session)
    other_tenant_id = await _make_organization(db_session)
    target_source_id = uuid.uuid4()
    other_source_id = uuid.uuid4()

    zero_vector = [0.0] * EMBEDDING_DIMENSIONS

    # Row that should be deleted.
    db_session.add(
        KnowledgeChunk(
            tenant_id=tenant_id,
            source_type="file",
            source_id=target_source_id,
            chunk_index=0,
            chunk_text="delete me",
            embedding=zero_vector,
        )
    )
    # Same tenant, different source -- must survive.
    db_session.add(
        KnowledgeChunk(
            tenant_id=tenant_id,
            source_type="file",
            source_id=other_source_id,
            chunk_index=0,
            chunk_text="keep me (different source)",
            embedding=zero_vector,
        )
    )
    # Different tenant, same source id -- must survive (tenant_id is part
    # of the delete's WHERE clause, not just source_type/source_id).
    db_session.add(
        KnowledgeChunk(
            tenant_id=other_tenant_id,
            source_type="file",
            source_id=target_source_id,
            chunk_index=0,
            chunk_text="keep me (different tenant)",
            embedding=zero_vector,
        )
    )
    await db_session.flush()

    await delete_chunks_for_source(
        db_session, tenant_id=tenant_id, source_type="file", source_id=target_source_id
    )
    await db_session.flush()

    remaining = (await db_session.execute(select(KnowledgeChunk.chunk_text))).scalars().all()
    assert set(remaining) == {"keep me (different source)", "keep me (different tenant)"}
