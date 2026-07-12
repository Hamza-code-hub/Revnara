import uuid
from typing import Any

from sqlalchemy import JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_mixins import TenantScopedColumns


class ExplainabilityRecord(Base, TenantScopedColumns):
    """Sprint 7 (BE7.2/DB7.2, Blueprint §69): a generic, reusable "why"
    record for any AI-produced decision across the whole plan --
    qualification and team-match are the first two producers, but
    pricing/approvals/rejections in later sprints write here too rather
    than inventing their own explainability shape. `entity_type` +
    `entity_id` point at whatever row the decision is about (e.g.
    "qualification_result" + a QualificationResult.id).
    """

    __tablename__ = "explainability_records"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    decision: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    rules_applied: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    missing_data: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class OverrideRecord(Base, TenantScopedColumns):
    """Sprint 7 (BE7.6/DB7.3): captures every human correction of an
    AI-produced output as a structured row -- never a silent field
    overwrite. `created_by`/`created_at` (from [TenantScopedColumns])
    already carry actor/timestamp, so this table only adds what's
    specific to the correction itself. This is the primary data source
    Sprint 25's win/loss learning loop depends on ("where did the AI get
    it wrong") -- it didn't exist before this sprint.
    """

    __tablename__ = "override_records"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    original_value: Mapped[Any] = mapped_column(JSON, nullable=False)
    new_value: Mapped[Any] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
