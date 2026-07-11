import asyncio
import logging
import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import session_factory
from app.rag import queue
from app.rag.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from app.rag.ingestion import EMBEDDING_QUEUE_NAME
from app.rag.models import KnowledgeChunk
from app.rag.schemas import EmbeddingTask
from app.tenancy.pg_session import set_pg_tenant_context

logger = logging.getLogger(__name__)

_VISIBILITY_TIMEOUT_SECONDS = 60
_IDLE_POLL_SECONDS = 5


async def process_one(db: AsyncSession, embedder: EmbeddingProvider) -> bool:
    """Reads and processes a single embedding_task. Returns False if the
    queue was empty. Upserts on `uq_knowledge_chunk_source` (tenant_id,
    source_type, source_id, chunk_index) rather than plain INSERT -- a
    message redelivered after a crash (pgmq's visibility-timeout mechanism,
    not deletion) overwrites the same row instead of creating a duplicate
    vector, which is what actually makes "kill the worker mid-batch,
    restart, no duplicates" true (see docs/rag-pattern.md)."""
    messages = await queue.read(
        db, EMBEDDING_QUEUE_NAME, visibility_timeout_seconds=_VISIBILITY_TIMEOUT_SECONDS, quantity=1
    )
    if not messages:
        return False

    message = messages[0]
    task = EmbeddingTask.model_validate(message.payload)

    # See document_worker/main.py's identical call for why this is needed:
    # a worker session has no single "current tenant" the way a request's
    # does, and RLS applies to this INSERT the same as any other write on
    # the revnara_app connection.
    await set_pg_tenant_context(db, task.tenant_id)

    embeddings = await embedder.embed([task.chunk_text])

    stmt = pg_insert(KnowledgeChunk).values(
        id=uuid.uuid4(),
        tenant_id=task.tenant_id,
        workspace_id=task.workspace_id,
        source_type=task.source_type,
        source_id=task.resource_id,
        chunk_index=task.chunk_index,
        chunk_text=task.chunk_text,
        classification=task.classification,
        embedding=embeddings[0],
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_knowledge_chunk_source",
        set_={
            "chunk_text": stmt.excluded.chunk_text,
            "classification": stmt.excluded.classification,
            "embedding": stmt.excluded.embedding,
        },
    )
    await db.execute(stmt)

    logger.info(
        "embedding_worker: %s chunk %d embedded", task.resource_id, task.chunk_index
    )

    await queue.delete(db, EMBEDDING_QUEUE_NAME, message.msg_id)
    await db.commit()
    return True


async def run_forever() -> None:
    settings = get_settings()
    embedder = OpenAIEmbeddingProvider(api_key=settings.model_provider_api_key)
    while True:
        async with session_factory() as db:
            try:
                processed = await process_one(db, embedder)
            except Exception:
                logger.exception("embedding_worker: error processing task")
                await db.rollback()
                processed = True
        if not processed:
            await asyncio.sleep(_IDLE_POLL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
