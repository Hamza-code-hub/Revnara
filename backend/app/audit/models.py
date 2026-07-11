import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ActorType(enum.StrEnum):
    USER = "user"
    AGENT = "agent"
    SERVICE = "service"


class AuditOutcome(enum.StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class AuditEvent(Base):
    """Per docs/BDOS_Enforcement_Spec.md's "Audit Event Minimum Schema".

    Most fields below (agent_run_id, capability_id, policy_decisions,
    risk_assessment_id, approval_id, ...) don't have a producer yet --
    those land in Sprint 8-10's agent runtime and policy/risk engines.
    They're nullable and present now anyway so this table's shape doesn't
    need a breaking migration later; every sprint that adds a producer
    just starts populating an existing column.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    actor_type: Mapped[ActorType] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capability_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    connector_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)

    policy_decisions: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    risk_assessment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    approval_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_result_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    outcome: Mapped[AuditOutcome] = mapped_column(String(20), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
