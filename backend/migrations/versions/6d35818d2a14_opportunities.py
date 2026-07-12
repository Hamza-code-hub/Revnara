"""opportunities

Revision ID: 6d35818d2a14
Revises: 82641a4bc6d5
Create Date: 2026-07-12 05:56:16.430775

Sprint 6 (Opportunity Intake & Data Model, DB6.1): clients, contacts,
opportunity_sources, opportunities. RLS policies for these tables are
added in supabase/rls/, not here -- see supabase/README.md's "one schema
source of truth" rule.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6d35818d2a14'
down_revision: str | Sequence[str] | None = '82641a4bc6d5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'clients',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('research_brief', sa.Text(), nullable=True),
        sa.Column('research_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('retention_policy', sa.String(length=50), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_clients_tenant_id'), 'clients', ['tenant_id'], unique=False)

    op.create_table(
        'opportunity_sources',
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_url', sa.String(length=1000), nullable=True),
        sa.Column('raw_metadata', sa.JSON(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('retention_policy', sa.String(length=50), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_opportunity_sources_tenant_id'), 'opportunity_sources', ['tenant_id'],
        unique=False,
    )

    op.create_table(
        'contacts',
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('retention_policy', sa.String(length=50), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_contacts_tenant_id'), 'contacts', ['tenant_id'], unique=False)

    op.create_table(
        'opportunities',
        sa.Column('client_id', sa.Uuid(), nullable=True),
        sa.Column('source_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('budget_min', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('budget_max', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('budget_currency', sa.String(length=3), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('safety_screening_status', sa.String(length=20), nullable=False),
        sa.Column('safety_screening_flags', sa.JSON(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('retention_policy', sa.String(length=50), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['source_id'], ['opportunity_sources.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_opportunities_tenant_id'), 'opportunities', ['tenant_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_opportunities_tenant_id'), table_name='opportunities')
    op.drop_table('opportunities')
    op.drop_index(op.f('ix_contacts_tenant_id'), table_name='contacts')
    op.drop_table('contacts')
    op.drop_index(op.f('ix_opportunity_sources_tenant_id'), table_name='opportunity_sources')
    op.drop_table('opportunity_sources')
    op.drop_index(op.f('ix_clients_tenant_id'), table_name='clients')
    op.drop_table('clients')
