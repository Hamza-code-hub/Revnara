from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
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
from app.tenancy.pg_session import set_pg_actor_context
from app.tenancy.repository import scoped_to_tenant

router = APIRouter(tags=["organizations"])


@router.post("/organizations", response_model=OrganizationCreateResponse, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    current_user: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationCreateResponse:
    # No tenant yet -- creating one is exactly what this request does.
    # The RLS policy on `users` allows "create/see your own row"
    # unconditionally via current_actor_user_id(), which is why this is
    # set before get_or_create_user's lookup/insert below.
    await set_pg_actor_context(db, user_id=current_user.user_id)

    await service.get_or_create_user(
        db, user_id=current_user.user_id, email=current_user.email
    )
    organization, workspace = await service.create_organization(
        db, name=payload.name, creator_user_id=current_user.user_id
    )

    # BE3.4: first real usage of the audit writer -- if this write fails,
    # it raises and app.database.get_db_session rolls back the whole
    # request, including the organization/workspace/roles/membership rows
    # just created above (fail-closed, Enforcement Spec Core Rule #12).
    await write_audit_event(
        db,
        tenant_id=organization.id,
        actor_type=ActorType.USER,
        actor_id=current_user.user_id,
        action_type="organization.create",
        outcome=AuditOutcome.EXECUTED,
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
    # Deliberately no tenant context -- /me spans every organization the
    # user belongs to by design. The RLS SELECT policy on
    # organization_members allows "rows where I am the member"
    # independent of a single current tenant for exactly this endpoint.
    await set_pg_actor_context(db, user_id=current_user.user_id)

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
    result = await db.execute(scoped_to_tenant(select(Workspace), Workspace, tenant.tenant_id))
    return [WorkspaceRead.model_validate(w) for w in result.scalars().all()]
