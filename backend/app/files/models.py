import enum
import uuid

from sqlalchemy import BigInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_mixins import TenantScopedColumns


class FileStatus(enum.StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"


class File(Base, TenantScopedColumns):
    """Metadata row for a file whose bytes live in Supabase Storage (BE4.4)
    -- this table never stores file contents, only where they are
    (`bucket`/`storage_path`) and what they're attached to."""

    __tablename__ = "files"

    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[FileStatus] = mapped_column(
        String(20), default=FileStatus.PENDING, nullable=False
    )
    linked_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linked_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
