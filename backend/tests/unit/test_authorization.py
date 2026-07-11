import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenClaims
from app.organizations.authorization import require_permission
from app.organizations.models import Organization, OrganizationMember, Permission, Role
from app.tenancy.middleware import resolve_tenant_context


async def _seed_membership_with_permissions(
    db: AsyncSession, *, permission_keys: list[str]
) -> tuple[uuid.UUID, uuid.UUID]:
    org = Organization(name="Acme")
    db.add(org)
    await db.flush()

    permissions = []
    for key in permission_keys:
        permission = Permission(key=key, description=key)
        db.add(permission)
        permissions.append(permission)
    await db.flush()

    role = Role(tenant_id=org.id, name="custom", is_system_role=False, permissions=permissions)
    db.add(role)
    await db.flush()

    user_id = uuid.uuid4()
    member = OrganizationMember(tenant_id=org.id, user_id=user_id, role_id=role.id, status="active")
    db.add(member)
    await db.flush()

    return org.id, user_id


@pytest.mark.asyncio
async def test_role_with_permission_passes(db_session: AsyncSession) -> None:
    org_id, user_id = await _seed_membership_with_permissions(
        db_session, permission_keys=["members.invite"]
    )

    dependency = require_permission("members.invite")
    tenant = await dependency(
        tenant=await resolve_tenant_context(
            x_organization_id=str(org_id),
            current_user=TokenClaims(user_id=user_id, email="user@example.com"),
            db=db_session,
        )
    )

    assert tenant.tenant_id == org_id


@pytest.mark.asyncio
async def test_role_without_permission_is_rejected(db_session: AsyncSession) -> None:
    org_id, user_id = await _seed_membership_with_permissions(
        db_session, permission_keys=["org.manage"]  # not members.invite
    )

    dependency = require_permission("members.invite")
    tenant = await resolve_tenant_context(
        x_organization_id=str(org_id),
        current_user=TokenClaims(user_id=user_id, email="user@example.com"),
        db=db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        await dependency(tenant=tenant)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_deactivated_membership_is_rejected_before_permission_check(
    db_session: AsyncSession,
) -> None:
    """Deactivation (BE2.9) is enforced by resolve_tenant_context, which
    require_permission depends on -- a deactivated member never even
    reaches the permission check itself."""
    org = Organization(name="Acme")
    db_session.add(org)
    await db_session.flush()

    permission = Permission(key="members.invite", description="Invite")
    db_session.add(permission)
    await db_session.flush()

    role = Role(tenant_id=org.id, name="owner", is_system_role=True, permissions=[permission])
    db_session.add(role)
    await db_session.flush()

    user_id = uuid.uuid4()
    member = OrganizationMember(
        tenant_id=org.id, user_id=user_id, role_id=role.id, status="deactivated"
    )
    db_session.add(member)
    await db_session.flush()

    dependency = require_permission("members.invite")
    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            tenant=await resolve_tenant_context(
                x_organization_id=str(org.id),
                current_user=TokenClaims(user_id=user_id, email="user@example.com"),
                db=db_session,
            )
        )

    assert exc_info.value.status_code == 403
