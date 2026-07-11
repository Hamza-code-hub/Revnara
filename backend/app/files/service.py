import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.files.models import File, FileStatus
from app.files.storage import SignedUpload, StorageProvider, build_tenant_storage_path
from app.tenancy.repository import scoped_to_tenant


async def create_pending_upload(
    db: AsyncSession,
    storage: StorageProvider,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID,
    bucket: str,
    filename: str,
    content_type: str | None,
    linked_entity_type: str | None,
    linked_entity_id: uuid.UUID | None,
) -> tuple[File, SignedUpload]:
    storage_path = build_tenant_storage_path(tenant_id, filename)

    file_record = File(
        tenant_id=tenant_id,
        created_by=created_by,
        bucket=bucket,
        storage_path=storage_path,
        original_filename=filename,
        content_type=content_type,
        status=FileStatus.PENDING,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        uploaded_by=created_by,
    )
    db.add(file_record)
    await db.flush()

    signed_upload = await storage.create_signed_upload_url(bucket=bucket, path=storage_path)
    return file_record, signed_upload


async def get_file(
    db: AsyncSession, *, tenant_id: uuid.UUID, file_id: uuid.UUID
) -> File | None:
    result = await db.execute(
        scoped_to_tenant(select(File), File, tenant_id).where(File.id == file_id)
    )
    return result.scalar_one_or_none()


async def list_files(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[File]:
    result = await db.execute(scoped_to_tenant(select(File), File, tenant_id))
    return list(result.scalars().all())


class FileAlreadyFinalizedError(Exception):
    """Raised when confirming a file that isn't PENDING anymore -- guards
    against a stale/replayed confirm request re-finalizing an upload
    (BE4.3 security testing task)."""


async def confirm_upload(
    db: AsyncSession, *, tenant_id: uuid.UUID, file_id: uuid.UUID, size_bytes: int | None
) -> File:
    file_record = await get_file(db, tenant_id=tenant_id, file_id=file_id)
    if file_record is None:
        raise LookupError("File not found.")
    if file_record.status != FileStatus.PENDING:
        raise FileAlreadyFinalizedError(f"File is already {file_record.status}.")

    file_record.status = FileStatus.UPLOADED
    file_record.size_bytes = size_bytes
    file_record.version += 1
    await db.flush()
    return file_record
