"""agent_runtime

Revision ID: 79b971d274a7
Revises: 2bb53136e1ab
Create Date: 2026-07-12 12:21:11.641610

Sprint 8 (Agent Runtime Foundation & Model Gateway): agent_runs (DB8.1,
BE8.7 -- one row per agent execution, the backbone of Blueprint §71
observability) and tool_actions (BE8.4/BE8.7 -- one row per tool-call
attempt, allowed or blocked). RLS policies for these tables are added in
supabase/rls/, not here -- see supabase/README.md's "one schema source
of truth" rule.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '79b971d274a7'
down_revision: str | Sequence[str] | None = '2bb53136e1ab'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('agent_version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=False),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('total_input_tokens', sa.Integer(), nullable=False),
        sa.Column('total_output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('tool_call_count', sa.Integer(), nullable=False),
        sa.Column('halt_reason', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(op.f('ix_agent_runs_tenant_id'), 'agent_runs', ['tenant_id'], unique=False)

    op.create_table(
        'tool_actions',
        sa.Column('agent_run_id', sa.Uuid(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('was_allowed', sa.Boolean(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_tool_actions_tenant_id'), 'tool_actions', ['tenant_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_tool_actions_tenant_id'), table_name='tool_actions')
    op.drop_table('tool_actions')
    op.drop_index(op.f('ix_agent_runs_tenant_id'), table_name='agent_runs')
    op.drop_table('agent_runs')
