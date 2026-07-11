"""knowledge_chunks

Revision ID: 82641a4bc6d5
Revises: 036d51bf76d3
Create Date: 2026-07-11 21:47:10.067575

Sprint 5 (Company Brain Retrieval / RAG, DB5.1/DB5.2): enables the
`vector` and `pgmq` extensions (idempotent -- already enabled by hand
against the real project during development, see supabase/README.md) and
creates `knowledge_chunks`. Queue creation itself (`pgmq.create(...)`)
requires extension-owner privilege, which the app's own `revnara_app` role
deliberately doesn't have -- see supabase/config/rag_queues.sql, run once
by the project's admin role, same as `storage_buckets.sql`.
"""
from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '82641a4bc6d5'
down_revision: str | Sequence[str] | None = '036d51bf76d3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgmq")

    op.create_table(
        'knowledge_chunks',
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Uuid(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=False),
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
        sa.UniqueConstraint(
            'tenant_id', 'source_type', 'source_id', 'chunk_index',
            name='uq_knowledge_chunk_source',
        ),
    )
    op.create_index(
        op.f('ix_knowledge_chunks_tenant_id'), 'knowledge_chunks', ['tenant_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_chunks_tenant_id'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    # Extensions deliberately not dropped -- pgmq's queue tables and any
    # other future vector column would be destroyed with them, which is
    # far more destructive than a normal migration downgrade should be.
