import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
from app.company import service
from app.company.models import CaseStudy, PortfolioItem, Skill, TeamMember
from app.company.schemas import (
    CaseStudyCreate,
    CaseStudyRead,
    CaseStudyUpdate,
    OrganizationProfileUpdate,
    PortfolioItemCreate,
    PortfolioItemRead,
    PortfolioItemUpdate,
    SkillCreate,
    SkillRead,
    SkillUpdate,
    TeamMemberCreate,
    TeamMemberRead,
    TeamMemberUpdate,
)
from app.company.service import sync_team_member_skills
from app.database import get_db_session
from app.organizations.authorization import require_permission
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationRead
from app.rag.ingestion import delete_chunks_for_source, enqueue_embedding_tasks
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context
from app.tenancy.repository import scoped_to_tenant

router = APIRouter(tags=["company"])


def _check_tenant(organization_id: uuid.UUID, tenant: TenantContext) -> None:
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")


async def _enqueue_portfolio_item_embedding(
    db: AsyncSession, *, organization_id: uuid.UUID, item: PortfolioItem
) -> None:
    """Portfolio items already hold plain text (no file to parse), so this
    goes straight to embedding_tasks -- no document_worker step needed,
    unlike file uploads (app/files/service.py's confirm_upload)."""
    text = " ".join(part for part in (item.title, item.description) if part)
    await enqueue_embedding_tasks(
        db,
        tenant_id=organization_id,
        workspace_id=item.workspace_id,
        source_type="portfolio_item",
        source_id=item.id,
        text=text,
        classification=item.classification,
        source_version=item.version,
    )


async def _enqueue_case_study_embedding(
    db: AsyncSession, *, organization_id: uuid.UUID, case_study: CaseStudy
) -> None:
    text = " ".join(
        part
        for part in (case_study.title, case_study.summary, case_study.content)
        if part
    )
    await enqueue_embedding_tasks(
        db,
        tenant_id=organization_id,
        workspace_id=case_study.workspace_id,
        source_type="case_study",
        source_id=case_study.id,
        text=text,
        classification=case_study.classification,
        source_version=case_study.version,
    )


# --- Company profile (fields on Organization itself) -----------------------


@router.get("/organizations/{organization_id}", response_model=OrganizationRead)
async def get_organization_profile(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationRead:
    _check_tenant(organization_id, tenant)

    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    organization = result.scalar_one_or_none()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    return OrganizationRead.model_validate(organization)


@router.patch("/organizations/{organization_id}", response_model=OrganizationRead)
async def update_organization_profile(
    organization_id: uuid.UUID,
    payload: OrganizationProfileUpdate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationRead:
    _check_tenant(organization_id, tenant)

    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    organization = result.scalar_one_or_none()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(organization, field, value)
    organization.version += 1
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="organization.profile_update",
        outcome=AuditOutcome.EXECUTED,
    )

    return OrganizationRead.model_validate(organization)


# --- Skills ------------------------------------------------------------


@router.get("/organizations/{organization_id}/skills", response_model=list[SkillRead])
async def list_skills(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[SkillRead]:
    _check_tenant(organization_id, tenant)
    skills = await service.list_skills(db, tenant_id=organization_id)
    return [SkillRead.model_validate(s) for s in skills]


@router.post("/organizations/{organization_id}/skills", response_model=SkillRead, status_code=201)
async def create_skill(
    organization_id: uuid.UUID,
    payload: SkillCreate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> SkillRead:
    _check_tenant(organization_id, tenant)
    skill = await service.create_skill(
        db,
        tenant_id=organization_id,
        created_by=tenant.user_id,
        name=payload.name,
        category=payload.category,
    )
    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="skill.create",
        outcome=AuditOutcome.EXECUTED,
    )
    return SkillRead.model_validate(skill)


@router.patch("/organizations/{organization_id}/skills/{skill_id}", response_model=SkillRead)
async def update_skill(
    organization_id: uuid.UUID,
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> SkillRead:
    _check_tenant(organization_id, tenant)
    skill = await _get_skill_or_404(db, organization_id=organization_id, skill_id=skill_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    skill.version += 1
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="skill.update",
        outcome=AuditOutcome.EXECUTED,
    )
    return SkillRead.model_validate(skill)


@router.delete("/organizations/{organization_id}/skills/{skill_id}", status_code=204)
async def delete_skill(
    organization_id: uuid.UUID,
    skill_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    _check_tenant(organization_id, tenant)
    skill = await _get_skill_or_404(db, organization_id=organization_id, skill_id=skill_id)

    await db.delete(skill)
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="skill.delete",
        outcome=AuditOutcome.EXECUTED,
    )


async def _get_skill_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, skill_id: uuid.UUID
) -> Skill:
    result = await db.execute(
        scoped_to_tenant(select(Skill), Skill, organization_id).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    return skill


# --- Team members --------------------------------------------------------


@router.get(
    "/organizations/{organization_id}/team-members", response_model=list[TeamMemberRead]
)
async def list_team_members(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[TeamMemberRead]:
    _check_tenant(organization_id, tenant)
    members = await service.list_team_members(db, tenant_id=organization_id)
    return [TeamMemberRead.model_validate(m) for m in members]


@router.post(
    "/organizations/{organization_id}/team-members",
    response_model=TeamMemberRead,
    status_code=201,
)
async def create_team_member(
    organization_id: uuid.UUID,
    payload: TeamMemberCreate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> TeamMemberRead:
    _check_tenant(organization_id, tenant)
    member = await service.create_team_member(
        db,
        tenant_id=organization_id,
        created_by=tenant.user_id,
        name=payload.name,
        title=payload.title,
        email=payload.email,
        bio=payload.bio,
        hourly_rate=payload.hourly_rate,
        currency=payload.currency,
        weekly_availability_hours=payload.weekly_availability_hours,
        skill_ids=payload.skill_ids,
    )
    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="team_member.create",
        outcome=AuditOutcome.EXECUTED,
    )
    return TeamMemberRead.model_validate(member)


@router.patch(
    "/organizations/{organization_id}/team-members/{team_member_id}",
    response_model=TeamMemberRead,
)
async def update_team_member(
    organization_id: uuid.UUID,
    team_member_id: uuid.UUID,
    payload: TeamMemberUpdate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> TeamMemberRead:
    _check_tenant(organization_id, tenant)
    member = await _get_team_member_or_404(
        db, organization_id=organization_id, team_member_id=team_member_id
    )

    updates = payload.model_dump(exclude_unset=True, exclude={"skill_ids"})
    for field, value in updates.items():
        setattr(member, field, value)
    member.version += 1
    await db.flush()

    if payload.skill_ids is not None:
        await sync_team_member_skills(
            db, team_member_id=member.id, skill_ids=payload.skill_ids
        )
        await db.refresh(member, attribute_names=["skills"])

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="team_member.update",
        outcome=AuditOutcome.EXECUTED,
    )
    return TeamMemberRead.model_validate(member)


@router.delete(
    "/organizations/{organization_id}/team-members/{team_member_id}", status_code=204
)
async def delete_team_member(
    organization_id: uuid.UUID,
    team_member_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    _check_tenant(organization_id, tenant)
    member = await _get_team_member_or_404(
        db, organization_id=organization_id, team_member_id=team_member_id
    )

    await db.delete(member)
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="team_member.delete",
        outcome=AuditOutcome.EXECUTED,
    )


async def _get_team_member_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, team_member_id: uuid.UUID
) -> TeamMember:
    result = await db.execute(
        scoped_to_tenant(select(TeamMember), TeamMember, organization_id)
        .options(selectinload(TeamMember.skills))
        .where(TeamMember.id == team_member_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found.")
    return member


# --- Portfolio items ------------------------------------------------------


@router.get(
    "/organizations/{organization_id}/portfolio-items",
    response_model=list[PortfolioItemRead],
)
async def list_portfolio_items(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[PortfolioItemRead]:
    _check_tenant(organization_id, tenant)
    items = await service.list_portfolio_items(db, tenant_id=organization_id)
    return [PortfolioItemRead.model_validate(i) for i in items]


@router.post(
    "/organizations/{organization_id}/portfolio-items",
    response_model=PortfolioItemRead,
    status_code=201,
)
async def create_portfolio_item(
    organization_id: uuid.UUID,
    payload: PortfolioItemCreate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> PortfolioItemRead:
    _check_tenant(organization_id, tenant)
    item = PortfolioItem(
        tenant_id=organization_id,
        created_by=tenant.user_id,
        **payload.model_dump(),
    )
    db.add(item)
    await db.flush()

    await _enqueue_portfolio_item_embedding(db, organization_id=organization_id, item=item)

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="portfolio_item.create",
        outcome=AuditOutcome.EXECUTED,
    )
    return PortfolioItemRead.model_validate(item)


@router.patch(
    "/organizations/{organization_id}/portfolio-items/{portfolio_item_id}",
    response_model=PortfolioItemRead,
)
async def update_portfolio_item(
    organization_id: uuid.UUID,
    portfolio_item_id: uuid.UUID,
    payload: PortfolioItemUpdate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> PortfolioItemRead:
    _check_tenant(organization_id, tenant)
    item = await _get_portfolio_item_or_404(
        db, organization_id=organization_id, portfolio_item_id=portfolio_item_id
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.version += 1
    await db.flush()

    await _enqueue_portfolio_item_embedding(db, organization_id=organization_id, item=item)

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="portfolio_item.update",
        outcome=AuditOutcome.EXECUTED,
    )
    return PortfolioItemRead.model_validate(item)


@router.delete(
    "/organizations/{organization_id}/portfolio-items/{portfolio_item_id}", status_code=204
)
async def delete_portfolio_item(
    organization_id: uuid.UUID,
    portfolio_item_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    _check_tenant(organization_id, tenant)
    item = await _get_portfolio_item_or_404(
        db, organization_id=organization_id, portfolio_item_id=portfolio_item_id
    )

    await delete_chunks_for_source(
        db, tenant_id=organization_id, source_type="portfolio_item", source_id=item.id
    )
    await db.delete(item)
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="portfolio_item.delete",
        outcome=AuditOutcome.EXECUTED,
    )


async def _get_portfolio_item_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, portfolio_item_id: uuid.UUID
) -> PortfolioItem:
    result = await db.execute(
        scoped_to_tenant(select(PortfolioItem), PortfolioItem, organization_id).where(
            PortfolioItem.id == portfolio_item_id
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio item not found."
        )
    return item


# --- Case studies ----------------------------------------------------------


@router.get(
    "/organizations/{organization_id}/case-studies", response_model=list[CaseStudyRead]
)
async def list_case_studies(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[CaseStudyRead]:
    _check_tenant(organization_id, tenant)
    case_studies = await service.list_case_studies(db, tenant_id=organization_id)
    return [CaseStudyRead.model_validate(c) for c in case_studies]


@router.post(
    "/organizations/{organization_id}/case-studies",
    response_model=CaseStudyRead,
    status_code=201,
)
async def create_case_study(
    organization_id: uuid.UUID,
    payload: CaseStudyCreate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> CaseStudyRead:
    _check_tenant(organization_id, tenant)
    case_study = CaseStudy(
        tenant_id=organization_id,
        created_by=tenant.user_id,
        **payload.model_dump(),
    )
    db.add(case_study)
    await db.flush()

    await _enqueue_case_study_embedding(db, organization_id=organization_id, case_study=case_study)

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="case_study.create",
        outcome=AuditOutcome.EXECUTED,
    )
    return CaseStudyRead.model_validate(case_study)


@router.patch(
    "/organizations/{organization_id}/case-studies/{case_study_id}",
    response_model=CaseStudyRead,
)
async def update_case_study(
    organization_id: uuid.UUID,
    case_study_id: uuid.UUID,
    payload: CaseStudyUpdate,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> CaseStudyRead:
    _check_tenant(organization_id, tenant)
    case_study = await _get_case_study_or_404(
        db, organization_id=organization_id, case_study_id=case_study_id
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case_study, field, value)
    case_study.version += 1
    await db.flush()

    await _enqueue_case_study_embedding(db, organization_id=organization_id, case_study=case_study)

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="case_study.update",
        outcome=AuditOutcome.EXECUTED,
    )
    return CaseStudyRead.model_validate(case_study)


@router.delete(
    "/organizations/{organization_id}/case-studies/{case_study_id}", status_code=204
)
async def delete_case_study(
    organization_id: uuid.UUID,
    case_study_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("company.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    _check_tenant(organization_id, tenant)
    case_study = await _get_case_study_or_404(
        db, organization_id=organization_id, case_study_id=case_study_id
    )

    await delete_chunks_for_source(
        db, tenant_id=organization_id, source_type="case_study", source_id=case_study.id
    )
    await db.delete(case_study)
    await db.flush()

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="case_study.delete",
        outcome=AuditOutcome.EXECUTED,
    )


async def _get_case_study_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, case_study_id: uuid.UUID
) -> CaseStudy:
    result = await db.execute(
        scoped_to_tenant(select(CaseStudy), CaseStudy, organization_id).where(
            CaseStudy.id == case_study_id
        )
    )
    case_study = result.scalar_one_or_none()
    if case_study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case study not found.")
    return case_study
