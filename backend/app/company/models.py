import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_mixins import TenantScopedColumns


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Skill(Base, TenantScopedColumns):
    """A tenant-defined catalog entry (e.g. "Flutter", "Kubernetes") --
    not a global taxonomy, since different software houses categorize
    skills differently (BE4.1)."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_skill_tenant_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)


class TeamMember(Base, TenantScopedColumns):
    __tablename__ = "team_members"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    weekly_availability_hours: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    skills: Mapped[list["Skill"]] = relationship(secondary="team_member_skills")


class TeamMemberSkill(Base):
    """Pure join table, same pattern as [app.organizations.models.RolePermission]
    -- no tenant_id of its own, RLS reaches through to team_members.tenant_id
    (see supabase/rls/team_member_skills.sql)."""

    __tablename__ = "team_member_skills"
    __table_args__ = (
        UniqueConstraint("team_member_id", "skill_id", name="uq_team_member_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("team_members.id"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skills.id"), nullable=False)
    proficiency_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class PortfolioItem(Base, TenantScopedColumns):
    __tablename__ = "portfolio_items"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    technologies: Mapped[str | None] = mapped_column(String(500), nullable=True)
    project_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CaseStudy(Base, TenantScopedColumns):
    """`classification` (a [TenantScopedColumns] common column, e.g.
    "public"/"confidential") is what marks a case study safe or unsafe to
    cite in a proposal for a different client -- deliberately not a
    separate `is_confidential` flag, since that's exactly what
    `classification` already exists to carry (BE9.4b relies on this)."""

    __tablename__ = "case_studies"

    portfolio_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("portfolio_items.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio_item: Mapped[PortfolioItem | None] = relationship()
