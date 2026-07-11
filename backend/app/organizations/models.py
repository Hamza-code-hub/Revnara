import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_mixins import TenantScopedColumns


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MemberStatus(enum.StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    DEACTIVATED = "deactivated"


class Organization(Base):
    """The tenant itself. Deliberately does NOT use [TenantScopedColumns]:
    `tenant_id`/`workspace_id` describe which tenant a row belongs to, and
    that's a category error for the tenant row itself -- Sprint 3's RLS
    policy for this table filters on `id`, not `tenant_id`.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retention_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(back_populates="organization")
    members: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="organization"
    )


class Workspace(Base, TenantScopedColumns):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    organization: Mapped[Organization] = relationship(
        back_populates="workspaces",
        primaryjoin="Workspace.tenant_id == Organization.id",
        foreign_keys="Workspace.tenant_id",
    )


class User(Base):
    """Global identity mirroring the Supabase Auth user -- NOT
    tenant-scoped, since one user can belong to multiple organizations via
    [OrganizationMember]. `id` is the Supabase Auth user id (JWT `sub`).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Role(Base, TenantScopedColumns):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[Organization] = relationship(
        back_populates="roles",
        primaryjoin="Role.tenant_id == Organization.id",
        foreign_keys="Role.tenant_id",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )


class Permission(Base):
    """Global permission catalog -- permission keys are code-defined
    capabilities (e.g. "members.invite"), not something a tenant defines
    itself, so unlike [Role] this is not tenant-scoped.
    """

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    roles: Mapped[list[Role]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id"), nullable=False
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("permissions.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class OrganizationMember(Base, TenantScopedColumns):
    __tablename__ = "organization_members"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roles.id"), nullable=False)
    status: Mapped[MemberStatus] = mapped_column(
        String(20), default=MemberStatus.PENDING, nullable=False
    )
    # Set for pending invitations where the invitee has not signed up yet
    # (user_id is null until they accept and a User row is created/linked).
    invited_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    organization: Mapped[Organization] = relationship(
        back_populates="members",
        primaryjoin="OrganizationMember.tenant_id == Organization.id",
        foreign_keys="OrganizationMember.tenant_id",
    )
    user: Mapped[User | None] = relationship()
    role: Mapped[Role] = relationship()
