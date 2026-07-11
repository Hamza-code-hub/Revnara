import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenClaims
from app.organizations.models import MemberStatus, Organization, OrganizationMember, Role
from app.tenancy.middleware import resolve_tenant_context


async def _seed_membership(
    db: AsyncSession, *, status: MemberStatus = MemberStatus.ACTIVE
) -> tuple[uuid.UUID, uuid.UUID]:
    """Creates an organization, a role, and a membership row directly
    (bypassing the API) so tenancy-resolution logic can be tested in
    isolation from the invite/create-org flows that normally produce them.
    Returns (organization_id, user_id).
    """
    org = Organization(name="Acme")
    db.add(org)
    await db.flush()

    role = Role(tenant_id=org.id, name="owner", is_system_role=True)
    db.add(role)
    await db.flush()

    user_id = uuid.uuid4()
    member = OrganizationMember(
        tenant_id=org.id, user_id=user_id, role_id=role.id, status=status
    )
    db.add(member)
    await db.flush()

    return org.id, user_id


@pytest.mark.asyncio
async def test_user_with_active_membership_resolves_tenant_context(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _seed_membership(db_session)

    context = await resolve_tenant_context(
        x_organization_id=str(org_id),
        current_user=TokenClaims(user_id=user_id, email="owner@example.com"),
        db=db_session,
    )

    assert context.tenant_id == org_id
    assert context.user_id == user_id
    assert context.role_name == "owner"


@pytest.mark.asyncio
async def test_user_with_no_membership_raises_403(db_session: AsyncSession) -> None:
    org = Organization(name="Acme")
    db_session.add(org)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await resolve_tenant_context(
            x_organization_id=str(org.id),
            current_user=TokenClaims(user_id=uuid.uuid4(), email="stranger@example.com"),
            db=db_session,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_deactivated_member_is_blocked(db_session: AsyncSession) -> None:
    """BE2.9: deactivation blocks any further authorization checks --
    verified here directly against the resolution logic every authenticated
    endpoint depends on, not assumed from the deactivate endpoint alone.
    """
    org_id, user_id = await _seed_membership(db_session, status=MemberStatus.DEACTIVATED)

    with pytest.raises(HTTPException) as exc_info:
        await resolve_tenant_context(
            x_organization_id=str(org_id),
            current_user=TokenClaims(user_id=user_id, email="owner@example.com"),
            db=db_session,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_pending_member_is_blocked(db_session: AsyncSession) -> None:
    """A pending invitation is not yet an active membership -- resolving
    tenant context must fail until the invite is accepted."""
    org_id, user_id = await _seed_membership(db_session, status=MemberStatus.PENDING)

    with pytest.raises(HTTPException) as exc_info:
        await resolve_tenant_context(
            x_organization_id=str(org_id),
            current_user=TokenClaims(user_id=user_id, email="invitee@example.com"),
            db=db_session,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_organization_id_header_returns_400(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await resolve_tenant_context(
            x_organization_id="not-a-uuid",
            current_user=TokenClaims(user_id=uuid.uuid4(), email="user@example.com"),
            db=db_session,
        )

    assert exc_info.value.status_code == 400
