import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.jwt import TokenClaims
from app.database import get_db_session
from app.organizations.models import MemberStatus, OrganizationMember, Role
from app.tenancy.context import TenantContext


async def resolve_tenant_context(
    x_organization_id: str = Header(
        ..., description="Which organization (tenant) this request operates in."
    ),
    current_user: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TenantContext:
    """Resolves the caller's active membership in the organization named by
    the `X-Organization-Id` header -- required explicitly rather than
    guessed from "the user's first org", since a user can belong to more
    than one tenant and the boundary must never be inferred implicitly.

    Raises 403 if the user has no *active* membership in that organization
    (covers: never joined, pending invite not yet accepted, or
    deactivated -- BE2.9's "deactivation blocks further authorization
    checks" is enforced here, on every request, not just at deactivation
    time).
    """
    try:
        tenant_id = uuid.UUID(x_organization_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-Id must be a valid UUID.",
        ) from exc

    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.role).selectinload(Role.permissions))
        .where(
            OrganizationMember.tenant_id == tenant_id,
            OrganizationMember.user_id == current_user.user_id,
            OrganizationMember.status == MemberStatus.ACTIVE,
        )
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active membership in this organization.",
        )

    return TenantContext(
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        role_id=membership.role_id,
        role_name=membership.role.name,
        permissions=frozenset(p.key for p in membership.role.permissions),
        workspace_id=membership.workspace_id,
    )
