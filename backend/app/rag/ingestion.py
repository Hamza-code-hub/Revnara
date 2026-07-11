import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import queue
from app.rag.chunking import chunk_text
from app.rag.models import KnowledgeChunk
from app.rag.schemas import EmbeddingTask

DOCUMENT_QUEUE_NAME = "document_tasks"
EMBEDDING_QUEUE_NAME = "embedding_tasks"


async def enqueue_embedding_tasks(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    workspace_id: uuid.UUID | None,
    source_type: str,
    source_id: uuid.UUID,
    text: str,
    classification: str | None,
    source_version: int = 1,
) -> int:
    """Chunks `text` and enqueues one embedding_task per chunk (BE5.1/5.2).
    The idempotency key is derived purely from (source_id, chunk_index,
    source_version) -- reprocessing the *same* source version always
    produces the same keys, which is what lets the embedding worker upsert
    instead of duplicate on a retried/redelivered message. Returns the
    number of chunks enqueued.
    """
    chunks = chunk_text(text)
    for index, chunk in enumerate(chunks):
        task = EmbeddingTask(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            task_id=uuid.uuid4(),
            resource_id=source_id,
            idempotency_key=f"{source_id}:{index}:v{source_version}",
            source_type=source_type,
            chunk_index=index,
            chunk_text=chunk,
            classification=classification,
        )
        await queue.send(db, EMBEDDING_QUEUE_NAME, task.model_dump(mode="json"))
    return len(chunks)


async def delete_chunks_for_source(
    db: AsyncSession, *, tenant_id: uuid.UUID, source_type: str, source_id: uuid.UUID
) -> None:
    """Deletion propagation (BE5.5): removes every knowledge_chunks row for
    a source once the source itself is deleted. An application-level
    delete, not a DB cascade -- source_type/source_id is a polymorphic
    reference (files, portfolio_items, or case_studies) with no single FK
    target for a cascade to attach to. Called from each of those entities'
    delete endpoints.
    """
    await db.execute(
        sql_delete(KnowledgeChunk).where(
            KnowledgeChunk.tenant_id == tenant_id,
            KnowledgeChunk.source_type == source_type,
            KnowledgeChunk.source_id == source_id,
        )
    )
