import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_mixins import TenantScopedColumns


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AgentRunStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


class AgentRun(Base, TenantScopedColumns):
    """BE8.7: every agent execution is a row -- the backbone of Blueprint
    §71 observability. `halted` (distinct from `failed`) means a
    configured limit (max_tool_calls/runtime/tokens/cost) was hit and the
    run stopped cleanly on purpose, not that something broke."""

    __tablename__ = "agent_runs"

    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(String(20), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    halt_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolAction(Base, TenantScopedColumns):
    """BE8.4/BE8.7: one row per tool-call attempt within a run, whether it
    was allowed or blocked -- a blocked attempt is recorded here (and
    audited, app/audit/writer.py) exactly like an allowed one, since
    "the agent tried to call a tool it wasn't allowed to" is itself
    security-relevant history, not something to discard."""

    __tablename__ = "tool_actions"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agent_runs.id"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    was_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
