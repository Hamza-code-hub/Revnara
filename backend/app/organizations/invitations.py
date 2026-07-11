import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.organizations.models import MemberStatus, OrganizationMember, Role, User
from app.organizations.schemas import InvitationCreate, MemberRead, MemberRoleUpdate
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context

router = APIRouter(tags=["organization-members"])


def _require_permission(tenant: TenantContext, permission_key: str) -> None:
    """Inline permission check for Sprint 2 -- Sprint 3 formalizes this
    into a shared `require_permission` FastAPI dependency (per the sprint
    plan); this function is written so that formalization is a
    call-site-only change, not a rewrite of the check itself.
    """
    if not tenant.has_permission(permission_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission_key}",
        )


async def _get_role_by_name(db: AsyncSession, *, tenant_id: uuid.UUID, name: str) -> Role:
    result = await db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.name == name)
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: {name}",
        )
    return role


@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=MemberRead,
    status_code=201,
)
async def invite_member(
    organization_id: uuid.UUID,
    payload: InvitationCreate,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> MemberRead:
    _require_permission(tenant, "members.invite")
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")

    role = await _get_role_by_name(db, tenant_id=organization_id, name=payload.role_name)

    existing_user_result = await db.execute(select(User).where(User.email == payload.email))
    existing_user = existing_user_result.scalar_one_or_none()

    member = OrganizationMember(
        tenant_id=organization_id,
        user_id=existing_user.id if existing_user else None,
        role_id=role.id,
        status=MemberStatus.PENDING,
        invited_email=payload.email,
        created_by=tenant.user_id,
    )
    db.add(member)
    await db.flush()

    # Actually dispatching the invite (Supabase Auth invite/magic-link
    # email) requires the Supabase Admin API and a real project -- not
    # available in this environment. The pending membership row above is
    # the durable state; wiring the email send is a follow-up once a real
    # Supabase project exists (§4 Environment Prerequisites).

    return MemberRead(
        id=member.id,
        user_id=member.user_id,
        email=payload.email,
        role_name=role.name,
        status=member.status,
        invited_email=member.invited_email,
    )


@router.get(
    "/organizations/{organization_id}/members",
    response_model=list[MemberRead],
)
async def list_members(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[MemberRead]:
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")

    result = await db.execute(
        select(OrganizationMember)
        .options(
            selectinload(OrganizationMember.role),
            selectinload(OrganizationMember.user),
        )
        .where(OrganizationMember.tenant_id == organization_id)
    )
    members = result.scalars().all()
    return [
        MemberRead(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email if m.user else m.invited_email,
            role_name=m.role.name,
            status=m.status,
            invited_email=m.invited_email,
        )
        for m in members
    ]


@router.patch(
    "/organizations/{organization_id}/members/{member_id}",
    response_model=MemberRead,
)
async def update_member_role(
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: MemberRoleUpdate,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> MemberRead:
    _require_permission(tenant, "members.manage_roles")
    member = await _get_member_or_404(db, organization_id=organization_id, member_id=member_id)

    role = await _get_role_by_name(db, tenant_id=organization_id, name=payload.role_name)
    member.role_id = role.id
    member.version += 1
    await db.flush()

    return MemberRead(
        id=member.id,
        user_id=member.user_id,
        email=member.user.email if member.user else member.invited_email,
        role_name=role.name,
        status=member.status,
        invited_email=member.invited_email,
    )


@router.delete(
    "/organizations/{organization_id}/members/{member_id}",
    status_code=204,
)
async def deactivate_member(
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft-deactivates a member -- never a hard delete of a user who has
    authored auditable records (BE2.8). The very next request this member
    makes will fail `resolve_tenant_context`'s active-status check (403),
    which is how BE2.9's "blocks any further authorization checks"
    requirement is actually enforced -- see
    tests/unit/test_tenancy_context.py.
    """
    _require_permission(tenant, "members.remove")
    member = await _get_member_or_404(db, organization_id=organization_id, member_id=member_id)

    member.status = MemberStatus.DEACTIVATED
    member.version += 1
    await db.flush()


async def _get_member_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, member_id: uuid.UUID
) -> OrganizationMember:
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(
            OrganizationMember.id == member_id,
            OrganizationMember.tenant_id == organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    return member
