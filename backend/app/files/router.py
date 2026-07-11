import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
from app.config import get_settings
from app.database import get_db_session
from app.files import service
from app.files.schemas import (
    FileConfirmRequest,
    FileRead,
    SignedUploadRequest,
    SignedUploadResponse,
)
from app.files.storage import StorageProvider, SupabaseStorageProvider
from app.organizations.authorization import require_permission
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context

router = APIRouter(tags=["files"])


def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    return SupabaseStorageProvider(
        base_url=settings.supabase_url, service_role_key=settings.supabase_service_role_key
    )


def _check_tenant(organization_id: uuid.UUID, tenant: TenantContext) -> None:
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")


@router.get("/organizations/{organization_id}/files", response_model=list[FileRead])
async def list_files(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[FileRead]:
    _check_tenant(organization_id, tenant)
    files = await service.list_files(db, tenant_id=organization_id)
    return [FileRead.model_validate(f) for f in files]


@router.post(
    "/organizations/{organization_id}/files/signed-upload",
    response_model=SignedUploadResponse,
    status_code=201,
)
async def create_signed_upload(
    organization_id: uuid.UUID,
    payload: SignedUploadRequest,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
    storage: StorageProvider = Depends(get_storage_provider),
) -> SignedUploadResponse:
    _check_tenant(organization_id, tenant)
    settings = get_settings()

    file_record, signed_upload = await service.create_pending_upload(
        db,
        storage,
        tenant_id=organization_id,
        created_by=tenant.user_id,
        bucket=settings.supabase_storage_bucket,
        filename=payload.filename,
        content_type=payload.content_type,
        linked_entity_type=payload.linked_entity_type,
        linked_entity_id=payload.linked_entity_id,
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="file.signed_upload_create",
        outcome=AuditOutcome.EXECUTED,
    )

    return SignedUploadResponse(
        file_id=file_record.id,
        upload_url=signed_upload.upload_url,
        token=signed_upload.token,
        storage_path=file_record.storage_path,
    )


@router.post(
    "/organizations/{organization_id}/files/{file_id}/confirm",
    response_model=FileRead,
)
async def confirm_upload(
    organization_id: uuid.UUID,
    file_id: uuid.UUID,
    payload: FileConfirmRequest,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> FileRead:
    _check_tenant(organization_id, tenant)

    try:
        file_record = await service.confirm_upload(
            db,
            tenant_id=organization_id,
            file_id=file_id,
            size_bytes=payload.size_bytes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except service.FileAlreadyFinalizedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="file.confirm",
        outcome=AuditOutcome.EXECUTED,
    )

    return FileRead.model_validate(file_record)


@router.delete("/organizations/{organization_id}/files/{file_id}", status_code=204)
async def delete_file(
    organization_id: uuid.UUID,
    file_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    _check_tenant(organization_id, tenant)

    try:
        await service.delete_file(db, tenant_id=organization_id, file_id=file_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="file.delete",
        outcome=AuditOutcome.EXECUTED,
    )
