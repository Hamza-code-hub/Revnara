import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.organizations.models import (
    MemberStatus,
    Organization,
    OrganizationMember,
    Permission,
    Role,
    User,
    Workspace,
)
from app.organizations.permissions_catalog import DEFAULT_ROLE_PERMISSIONS, PERMISSIONS


async def ensure_permission_catalog(db: AsyncSession) -> dict[str, Permission]:
    """Idempotently ensures every key in PERMISSIONS exists as a row.
    Global catalog, not tenant-scoped -- safe to call repeatedly (e.g. once
    per organization creation) since it only inserts missing keys.
    """
    result = await db.execute(select(Permission))
    existing = {p.key: p for p in result.scalars().all()}

    for key, description in PERMISSIONS.items():
        if key not in existing:
            permission = Permission(key=key, description=description)
            db.add(permission)
            existing[key] = permission

    await db.flush()
    return existing


async def create_organization(
    db: AsyncSession, *, name: str, creator_user_id: uuid.UUID
) -> tuple[Organization, Workspace]:
    """Creates an organization with its default workspace, default roles
    (owner/admin/member) with permission grants, and an active owner
    membership for the creator -- atomically (single flush; the caller's
    transaction commits or rolls back everything together, per Sprint 2's
    "rollback test: force a failure mid-transaction, confirm nothing
    partially persists" requirement).
    """
    permissions = await ensure_permission_catalog(db)

    organization = Organization(name=name, created_by=creator_user_id)
    db.add(organization)
    await db.flush()  # assigns organization.id

    workspace = Workspace(
        tenant_id=organization.id,
        name="Default",
        created_by=creator_user_id,
    )
    db.add(workspace)

    roles: dict[str, Role] = {}
    for role_name, permission_keys in DEFAULT_ROLE_PERMISSIONS.items():
        role = Role(
            tenant_id=organization.id,
            name=role_name,
            is_system_role=True,
            created_by=creator_user_id,
            permissions=[permissions[key] for key in permission_keys],
        )
        db.add(role)
        roles[role_name] = role

    await db.flush()  # assigns role ids

    owner_membership = OrganizationMember(
        tenant_id=organization.id,
        user_id=creator_user_id,
        role_id=roles["owner"].id,
        status=MemberStatus.ACTIVE,
        created_by=creator_user_id,
    )
    db.add(owner_membership)

    await db.flush()
    return organization, workspace


async def get_or_create_user(
    db: AsyncSession, *, user_id: uuid.UUID, email: str | None
) -> User:
    """Mirrors a Supabase Auth identity into the local `users` table on
    first sight -- the backend never creates Supabase Auth users itself,
    only local profile rows keyed by the same id (JWT `sub`).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(id=user_id, email=email or f"{user_id}@unknown.local")
    db.add(user)
    await db.flush()
    return user


async def get_my_memberships(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[OrganizationMember]:
    result = await db.execute(
        select(OrganizationMember)
        .options(
            selectinload(OrganizationMember.organization),
            selectinload(OrganizationMember.role),
        )
        .where(OrganizationMember.user_id == user_id)
    )
    return list(result.scalars().all())
