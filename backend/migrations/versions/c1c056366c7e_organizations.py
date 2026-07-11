"""organizations

Revision ID: c1c056366c7e
Revises: fa2c5f721e68
Create Date: 2026-07-11 12:15:04.157467

Creates the Sprint 2 identity/tenancy tables: organizations, workspaces,
users, roles, permissions, role_permissions, organization_members.
RLS policies for these tables are added in Sprint 3 (supabase/rls/), not
here -- this migration is schema only, per supabase/README.md's "one
schema source of truth" rule.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1c056366c7e"
down_revision: str | Sequence[str] | None = "fa2c5f721e68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common_columns() -> list[sa.Column]:
    """Columns shared by every tenant-scoped table (mirrors
    app/db_mixins.py's TenantScopedColumns, minus `id`/`tenant_id`, which
    each table declares itself since `tenant_id`'s FK target is the same
    for every table but must be added after `organizations` exists).
    """
    return [
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=50), nullable=True),
        sa.Column("retention_policy", sa.String(length=50), nullable=True),
        sa.Column("legal_hold", sa.Boolean(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=50), nullable=True),
        sa.Column("retention_policy", sa.String(length=50), nullable=True),
        sa.Column("legal_hold", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        *_common_columns(),
    )
    op.create_index("ix_workspaces_tenant_id", "workspaces", ["tenant_id"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_system_role", sa.Boolean(), nullable=False),
        *_common_columns(),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "permission_id", sa.Uuid(), sa.ForeignKey("permissions.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "organization_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("invited_email", sa.String(length=320), nullable=True),
        *_common_columns(),
    )
    op.create_index(
        "ix_organization_members_tenant_id", "organization_members", ["tenant_id"]
    )
    op.create_index(
        "ix_organization_members_user_id", "organization_members", ["user_id"]
    )


def downgrade() -> None:
    op.drop_table("organization_members")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("workspaces")
    op.drop_table("permissions")
    op.drop_table("users")
    op.drop_table("organizations")
