import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_mixins import TenantScopedColumns

# text-embedding-3-small's dimensionality (app/rag/embeddings.py) -- fixed
# at the column level since pgvector requires a declared vector size.
EMBEDDING_DIMENSIONS = 1536


class KnowledgeChunk(Base, TenantScopedColumns):
    """One retrievable, embedded chunk of company knowledge (Sprint 5,
    DB5.2). `source_type`/`source_id` is a polymorphic reference (no DB-
    level FK, since the source can be a `files` row, a `portfolio_items`
    row, or a `case_studies` row) -- deletion propagation
    (app/rag/ingestion.py's `delete_chunks_for_source`) is therefore an
    application-level concern, not a cascading FK.

    `classification` (the TenantScopedColumns common column) is what
    retrieval.py's permission filter checks -- a chunk classified
    "confidential" requires the caller to hold `company.manage`, mirroring
    the same permission that gates editing the underlying company brain
    data in the first place.
    """

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        # One row per (source, chunk_index) -- the embedding worker upserts
        # on this constraint (ON CONFLICT DO UPDATE), which is what makes
        # "kill the worker mid-batch, restart, confirm no duplicate
        # vectors" (Sprint 5 testing task) true by construction rather
        # than by hoping the worker never reprocesses a message twice.
        UniqueConstraint(
            "tenant_id", "source_type", "source_id", "chunk_index", name="uq_knowledge_chunk_source"
        ),
    )

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
