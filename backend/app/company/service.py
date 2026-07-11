import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.company.models import CaseStudy, PortfolioItem, Skill, TeamMember, TeamMemberSkill
from app.tenancy.repository import scoped_to_tenant


async def list_skills(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[Skill]:
    result = await db.execute(scoped_to_tenant(select(Skill), Skill, tenant_id))
    return list(result.scalars().all())


async def create_skill(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID,
    name: str,
    category: str | None,
) -> Skill:
    skill = Skill(tenant_id=tenant_id, name=name, category=category, created_by=created_by)
    db.add(skill)
    await db.flush()
    return skill


async def sync_team_member_skills(
    db: AsyncSession, *, team_member_id: uuid.UUID, skill_ids: list[uuid.UUID]
) -> None:
    await db.execute(
        delete(TeamMemberSkill).where(TeamMemberSkill.team_member_id == team_member_id)
    )
    for skill_id in skill_ids:
        db.add(TeamMemberSkill(team_member_id=team_member_id, skill_id=skill_id))
    await db.flush()


async def list_team_members(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[TeamMember]:
    result = await db.execute(
        scoped_to_tenant(select(TeamMember), TeamMember, tenant_id).options(
            selectinload(TeamMember.skills)
        )
    )
    return list(result.scalars().all())


async def create_team_member(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID,
    name: str,
    title: str | None,
    email: str | None,
    bio: str | None,
    hourly_rate: float | None,
    currency: str | None,
    weekly_availability_hours: int | None,
    skill_ids: list[uuid.UUID],
) -> TeamMember:
    member = TeamMember(
        tenant_id=tenant_id,
        created_by=created_by,
        name=name,
        title=title,
        email=email,
        bio=bio,
        hourly_rate=hourly_rate,
        currency=currency,
        weekly_availability_hours=weekly_availability_hours,
    )
    db.add(member)
    await db.flush()
    if skill_ids:
        await sync_team_member_skills(db, team_member_id=member.id, skill_ids=skill_ids)
        await db.refresh(member, attribute_names=["skills"])
    return member


async def list_portfolio_items(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[PortfolioItem]:
    result = await db.execute(scoped_to_tenant(select(PortfolioItem), PortfolioItem, tenant_id))
    return list(result.scalars().all())


async def list_case_studies(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[CaseStudy]:
    result = await db.execute(scoped_to_tenant(select(CaseStudy), CaseStudy, tenant_id))
    return list(result.scalars().all())
