import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import session_factory
from app.files.models import File, FileStatus
from app.files.storage import StorageProvider, SupabaseStorageProvider
from app.rag import queue
from app.rag.ingestion import DOCUMENT_QUEUE_NAME, enqueue_embedding_tasks
from app.rag.schemas import DocumentTask
from app.rag.text_extraction import extract_text
from app.tenancy.pg_session import set_pg_tenant_context

logger = logging.getLogger(__name__)

_VISIBILITY_TIMEOUT_SECONDS = 60
_IDLE_POLL_SECONDS = 5


async def process_one(db: AsyncSession, storage: StorageProvider) -> bool:
    """Reads and processes a single document_task. Returns False if the
    queue was empty (nothing to do), True otherwise -- callers use this to
    decide whether to poll again immediately or back off (BE5.1).
    """
    messages = await queue.read(
        db, DOCUMENT_QUEUE_NAME, visibility_timeout_seconds=_VISIBILITY_TIMEOUT_SECONDS, quantity=1
    )
    if not messages:
        return False

    message = messages[0]
    task = DocumentTask.model_validate(message.payload)

    # A worker's session has no single "current tenant" the way a
    # request's does -- it processes messages for whichever tenant each
    # task belongs to. Without setting this explicitly per task, RLS
    # (which applies to the worker's revnara_app connection exactly like
    # any other -- workers never bypass it) rejects the INSERT that
    # enqueue_embedding_tasks below performs. Found by actually running
    # this against a real Supabase project, not assumed.
    await set_pg_tenant_context(db, task.tenant_id)

    result = await db.execute(select(File).where(File.id == task.resource_id))
    file_record = result.scalar_one_or_none()

    if file_record is None or file_record.status != FileStatus.UPLOADED:
        # File was deleted, or never actually finished uploading, before
        # this task ran -- nothing to parse. Ack it rather than retrying
        # forever on a task that can never succeed.
        await queue.delete(db, DOCUMENT_QUEUE_NAME, message.msg_id)
        await db.commit()
        return True

    data = await storage.download_file(bucket=file_record.bucket, path=file_record.storage_path)
    text = extract_text(
        content_type=file_record.content_type,
        filename=file_record.original_filename,
        data=data,
    )

    chunk_count = await enqueue_embedding_tasks(
        db,
        tenant_id=file_record.tenant_id,
        workspace_id=file_record.workspace_id,
        source_type="file",
        source_id=file_record.id,
        text=text,
        classification=file_record.classification,
        source_version=file_record.version,
    )
    logger.info(
        "document_worker: file %s -> %d chunk(s) enqueued for embedding",
        file_record.id,
        chunk_count,
    )

    await queue.delete(db, DOCUMENT_QUEUE_NAME, message.msg_id)
    await db.commit()
    return True


async def run_forever() -> None:
    settings = get_settings()
    storage = SupabaseStorageProvider(
        base_url=settings.supabase_url, service_role_key=settings.supabase_service_role_key
    )
    while True:
        async with session_factory() as db:
            try:
                processed = await process_one(db, storage)
            except Exception:
                logger.exception("document_worker: error processing task")
                await db.rollback()
                processed = True  # don't idle-sleep after a real error either
        if not processed:
            await asyncio.sleep(_IDLE_POLL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
