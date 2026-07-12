"""qualification_matching

Revision ID: 2bb53136e1ab
Revises: 6d35818d2a14
Create Date: 2026-07-12 11:01:20.755806

Sprint 7 (Qualification, Team Matching & Pipeline UI): qualification_
results, team_match_results (DB7.1, ADR 0008 -- dedicated tables, not
JSONB columns on opportunities), explainability_records (DB7.2, generic
"why" record reused by every future AI decision), and override_records
(DB7.3, structured human-correction capture feeding Sprint 25's win/loss
learning loop). RLS policies for these tables are added in supabase/rls/,
not here -- see supabase/README.md's "one schema source of truth" rule.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2bb53136e1ab'
down_revision: str | Sequence[str] | None = '6d35818d2a14'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'explainability_records',
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('decision', sa.String(length=255), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('rules_applied', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('missing_data', sa.JSON(), nullable=False),
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
        op.f('ix_explainability_records_tenant_id'), 'explainability_records', ['tenant_id'],
        unique=False,
    )

    op.create_table(
        'override_records',
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('field', sa.String(length=100), nullable=False),
        sa.Column('original_value', sa.JSON(), nullable=False),
        sa.Column('new_value', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
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
        op.f('ix_override_records_tenant_id'), 'override_records', ['tenant_id'], unique=False
    )

    op.create_table(
        'qualification_results',
        sa.Column('opportunity_id', sa.Uuid(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('missing_info', sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('opportunity_id', name='uq_qualification_result_opportunity'),
    )
    op.create_index(
        op.f('ix_qualification_results_tenant_id'), 'qualification_results', ['tenant_id'],
        unique=False,
    )

    op.create_table(
        'team_match_results',
        sa.Column('opportunity_id', sa.Uuid(), nullable=False),
        sa.Column('recommended_team_member_ids', sa.JSON(), nullable=False),
        sa.Column('delivery_risk', sa.String(length=20), nullable=False),
        sa.Column('estimated_weekly_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('estimated_cost_currency', sa.String(length=3), nullable=True),
        sa.Column('gaps', sa.JSON(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('opportunity_id', name='uq_team_match_result_opportunity'),
    )
    op.create_index(
        op.f('ix_team_match_results_tenant_id'), 'team_match_results', ['tenant_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_team_match_results_tenant_id'), table_name='team_match_results')
    op.drop_table('team_match_results')
    op.drop_index(
        op.f('ix_qualification_results_tenant_id'), table_name='qualification_results'
    )
    op.drop_table('qualification_results')
    op.drop_index(op.f('ix_override_records_tenant_id'), table_name='override_records')
    op.drop_table('override_records')
    op.drop_index(
        op.f('ix_explainability_records_tenant_id'), table_name='explainability_records'
    )
    op.drop_table('explainability_records')
