"""Full document_worker -> embedding_worker pipeline against a real
Supabase project (see conftest.py's skip guard). Storage and the
embedding model are faked (no real Supabase Storage bytes or model
provider API key needed for this -- see app/rag/embeddings.py's
docstring), but the queue and the database are the real thing.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.files.models import File, FileStatus
from app.rag import queue
from app.rag.embeddings import EmbeddingProvider
from app.rag.models import EMBEDDING_DIMENSIONS, KnowledgeChunk
from app.rag.schemas import DocumentTask, EmbeddingTask
from tests.rag.conftest import cleanup_tenant, create_tenant, set_context
from workers.document_worker.main import process_one as process_one_document_task
from workers.embedding_worker.main import process_one as process_one_embedding_task


class _FakeStorage:
    def __init__(self, content: bytes) -> None:
        self._content = content
        self.download_calls = 0

    async def create_signed_upload_url(self, *, bucket: str, path: str):  # pragma: no cover
        raise NotImplementedError

    async def download_file(self, *, bucket: str, path: str) -> bytes:
        self.download_calls += 1
        return self._content


class _FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.call_count = 0

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[0.5] * EMBEDDING_DIMENSIONS for _ in texts]


@pytest.mark.asyncio
async def test_document_worker_parses_and_enqueues_embedding_tasks(
    pg_session: AsyncSession,
) -> None:
    org_id, owner_id = await create_tenant(pg_session, name=f"RAG Pipeline {uuid.uuid4()}")

    try:
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)

        file_record = File(
            tenant_id=org_id,
            bucket="company-files",
            storage_path=f"{org_id}/test.txt",
            original_filename="test.txt",
            content_type="text/plain",
            status=FileStatus.UPLOADED,
        )
        pg_session.add(file_record)
        await pg_session.flush()
        await pg_session.commit()

        task = DocumentTask(
            tenant_id=org_id,
            task_id=uuid.uuid4(),
            resource_id=file_record.id,
            idempotency_key=f"{file_record.id}:v1",
        )
        await queue.send(pg_session, "document_tasks", task.model_dump(mode="json"))
        await pg_session.commit()

        storage = _FakeStorage(b"hello from a real document worker test")
        processed = await process_one_document_task(pg_session, storage)

        assert processed is True
        assert storage.download_calls == 1

        messages = await queue.read(pg_session, "embedding_tasks", quantity=10)
        await pg_session.commit()
        matching = [m for m in messages if m.payload.get("resource_id") == str(file_record.id)]
        assert len(matching) == 1
        for m in matching:
            await queue.delete(pg_session, "embedding_tasks", m.msg_id)
        await pg_session.commit()
    finally:
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        await pg_session.execute(sql_delete(File).where(File.tenant_id == org_id))
        await pg_session.commit()
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)


@pytest.mark.asyncio
async def test_embedding_worker_crash_before_ack_does_not_duplicate_the_vector(
    pg_session: AsyncSession,
) -> None:
    """The actual "kill the worker mid-batch, restart, confirm no
    duplicate vectors" testing task: simulates a worker that successfully
    embeds and upserts a chunk but crashes before deleting the queue
    message (the realistic worst-case crash point), then proves the
    redelivered message -- processed again by the real process_one --
    results in exactly one row, not two."""
    org_id, owner_id = await create_tenant(pg_session, name=f"RAG Crash Test {uuid.uuid4()}")
    embedder = _FakeEmbeddingProvider()

    try:
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        source_id = uuid.uuid4()

        task = EmbeddingTask(
            tenant_id=org_id,
            task_id=uuid.uuid4(),
            resource_id=source_id,
            idempotency_key=f"{source_id}:0:v1",
            source_type="portfolio_item",
            chunk_index=0,
            chunk_text="this chunk survives a simulated worker crash",
            classification=None,
        )
        await queue.send(pg_session, "embedding_tasks", task.model_dump(mode="json"))
        await pg_session.commit()

        # First pass: read with a short visibility timeout and perform the
        # real embed-and-upsert work, but DON'T delete the message --
        # simulating a crash between the DB write and the queue ack.
        first_read = await queue.read(
            pg_session, "embedding_tasks", visibility_timeout_seconds=1, quantity=1
        )
        assert len(first_read) == 1
        embeddings = await embedder.embed([task.chunk_text])

        # queue.send's commit above ended the transaction that had tenant
        # context set -- re-set it before this manual insert, the same
        # fix needed throughout this file and test_retrieval_and_isolation.py.
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        stmt = pg_insert(KnowledgeChunk).values(
            id=uuid.uuid4(),
            tenant_id=org_id,
            source_type=task.source_type,
            source_id=source_id,
            chunk_index=task.chunk_index,
            chunk_text=task.chunk_text,
            classification=task.classification,
            embedding=embeddings[0],
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_knowledge_chunk_source",
            set_={"chunk_text": stmt.excluded.chunk_text, "embedding": stmt.excluded.embedding},
        )
        await pg_session.execute(stmt)
        await pg_session.commit()
        # Deliberately no queue.delete() here -- this is the "crash".

        await asyncio.sleep(1.5)  # let the visibility timeout elapse

        # Second pass: the real worker function, as it would run after a
        # restart, re-reads the now-redelivered message and reprocesses it.
        processed = await process_one_embedding_task(pg_session, embedder)
        assert processed is True
        assert embedder.call_count == 2, (
            "expected the chunk to actually be re-embedded, not skipped"
        )

        # process_one_embedding_task's own commit ended its transaction --
        # re-set context before this SELECT too, or RLS silently returns
        # zero rows instead of the real answer.
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        rows = (
            await pg_session.execute(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.tenant_id == org_id,
                    KnowledgeChunk.source_type == "portfolio_item",
                    KnowledgeChunk.source_id == source_id,
                )
            )
        ).scalars().all()
        assert len(rows) == 1, "crash-and-resume must not duplicate the vector row"
    finally:
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)
