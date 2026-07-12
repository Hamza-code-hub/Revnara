import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_mixins import TenantScopedColumns


def _utcnow() -> datetime:
    return datetime.now(UTC)


class OpportunityStatus(enum.StrEnum):
    """Drives Sprint 7's pipeline UI (DB6.2) -- the exact enum values are
    the contract that screen depends on, don't rename casually."""

    INTAKE = "intake"
    SCREENING = "screening"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    MATCHED = "matched"
    PROPOSING = "proposing"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    DISQUALIFIED = "disqualified"


class SafetyScreeningStatus(enum.StrEnum):
    """Separate from [OpportunityStatus] deliberately: an opportunity can
    sit at `status=screening` with either a clear or flagged screening
    outcome -- flagged ones stay there for human review (BE6.3's Demo
    Checklist: "show a flagged opportunity routed to review state"),
    rather than the pipeline stage itself encoding the review need."""

    PENDING = "pending_screening"
    CLEAR = "screened_clear"
    FLAGGED = "screened_flagged"


class OpportunitySourceType(enum.StrEnum):
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    UPWORK_LINK = "upwork_link"


class Client(Base, TenantScopedColumns):
    """The company/organization an opportunity is with. `research_brief`
    is BE6.5b's deterministic aggregation (app/opportunities/research.py)
    -- scoped to the client, not a single opportunity, since it's reused
    across every opportunity with the same client."""

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    research_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Contact(Base, TenantScopedColumns):
    __tablename__ = "contacts"

    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    client: Mapped[Client] = relationship()


class OpportunitySource(Base, TenantScopedColumns):
    """Lineage of how an opportunity was discovered/imported (Blueprint
    §35 Opportunity Normalization's "store source lineage"). `raw_metadata`
    holds whatever the intake method itself provided (e.g. the original
    CSV row) -- reference-only, never secrets/credentials, same rule as
    Sprint 5's queue messages."""

    __tablename__ = "opportunity_sources"

    source_type: Mapped[OpportunitySourceType] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class Opportunity(Base, TenantScopedColumns):
    __tablename__ = "opportunities"

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("clients.id"), nullable=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("opportunity_sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        String(20), default=OpportunityStatus.INTAKE, nullable=False
    )
    safety_screening_status: Mapped[SafetyScreeningStatus] = mapped_column(
        String(20), default=SafetyScreeningStatus.PENDING, nullable=False
    )
    safety_screening_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    client: Mapped[Client | None] = relationship()
    source: Mapped[OpportunitySource] = relationship()
