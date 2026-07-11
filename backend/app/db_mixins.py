import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TenantScopedColumns:
    """Common columns every business table carries, per
    docs/Revnara_Implementation_Plan.md §7. Mixed into a model alongside
    [app.database.Base], not a replacement for it.

    Uses SQLAlchemy's cross-dialect [Uuid] type (native `uuid` on
    Postgres, emulated on SQLite) so the same model works against both
    the real target (Postgres/Supabase) and the local SQLite test
    database -- see backend/tests/conftest.py.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        # A real FK, not just a loosely-typed column -- tenant scoping is a
        # referential-integrity concern, not only an RLS-policy one.
        return mapped_column(
            Uuid, ForeignKey("organizations.id"), index=True, nullable=False
        )


    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retention_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
