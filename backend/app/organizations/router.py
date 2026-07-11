from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import TokenClaims
from app.database import get_db_session
from app.organizations import service
from app.organizations.models import Workspace
from app.organizations.schemas import (
    MembershipRead,
    MeResponse,
    OrganizationCreate,
    OrganizationCreateResponse,
    OrganizationRead,
    WorkspaceRead,
)
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context

router = APIRouter(tags=["organizations"])


@router.post("/organizations", response_model=OrganizationCreateResponse, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    current_user: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationCreateResponse:
    await service.get_or_create_user(
        db, user_id=current_user.user_id, email=current_user.email
    )
    organization, workspace = await service.create_organization(
        db, name=payload.name, creator_user_id=current_user.user_id
    )
    return OrganizationCreateResponse(
        organization=OrganizationRead.model_validate(organization),
        workspace=WorkspaceRead.model_validate(workspace),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    memberships = await service.get_my_memberships(db, user_id=current_user.user_id)
    return MeResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        memberships=[
            MembershipRead(
                organization_id=m.tenant_id,
                organization_name=m.organization.name,
                role_name=m.role.name,
                workspace_id=m.workspace_id,
                status=m.status,
            )
            for m in memberships
        ],
    )


@router.get("/workspaces", response_model=list[WorkspaceRead])
async def list_workspaces(
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[WorkspaceRead]:
    result = await db.execute(
        select(Workspace).where(Workspace.tenant_id == tenant.tenant_id)
    )
    return [WorkspaceRead.model_validate(w) for w in result.scalars().all()]
