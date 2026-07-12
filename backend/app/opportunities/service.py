import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.company.models import Skill, TeamMember
from app.explainability.writer import write_explainability_record, write_override_record
from app.opportunities.models import (
    Client,
    Opportunity,
    OpportunitySource,
    OpportunitySourceType,
    OpportunityStatus,
    QualificationResult,
    SafetyScreeningStatus,
    TeamMatchResult,
)
from app.opportunities.pipeline import is_legal_transition
from app.opportunities.qualification import qualify_opportunity
from app.opportunities.safety_screening import screen_opportunity
from app.opportunities.team_matching import match_team
from app.tenancy.repository import scoped_to_tenant


class IllegalStatusTransitionError(ValueError):
    pass


class OpportunityFlaggedError(ValueError):
    pass


async def get_or_create_client(
    db: AsyncSession, *, tenant_id: uuid.UUID, created_by: uuid.UUID, name: str
) -> Client:
    result = await db.execute(
        scoped_to_tenant(select(Client), Client, tenant_id).where(Client.name == name)
    )
    client = result.scalar_one_or_none()
    if client is not None:
        return client

    client = Client(tenant_id=tenant_id, created_by=created_by, name=name)
    db.add(client)
    await db.flush()
    return client


async def create_opportunity(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID,
    source_type: OpportunitySourceType,
    title: str,
    description: str | None = None,
    requirements: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    budget_currency: str | None = None,
    client_name: str | None = None,
    external_id: str | None = None,
    external_url: str | None = None,
    raw_metadata: dict[str, Any] | None = None,
) -> Opportunity:
    """The single creation path every intake method (manual, CSV import,
    Upwork-link import) funnels through -- BE6.2/BE6.3: every new
    opportunity gets a source-lineage row and passes through safety
    screening before the row is ever returned to a caller.
    """
    source = OpportunitySource(
        tenant_id=tenant_id,
        created_by=created_by,
        source_type=source_type,
        external_id=external_id,
        external_url=external_url,
        raw_metadata=raw_metadata,
    )
    db.add(source)
    await db.flush()

    client = None
    if client_name:
        client = await get_or_create_client(
            db, tenant_id=tenant_id, created_by=created_by, name=client_name
        )

    screening = screen_opportunity(
        title=title,
        description=description,
        external_url=external_url,
        budget_min=budget_min,
        budget_max=budget_max,
    )

    opportunity = Opportunity(
        tenant_id=tenant_id,
        created_by=created_by,
        client_id=client.id if client else None,
        source_id=source.id,
        title=title,
        description=description,
        requirements=requirements,
        budget_min=budget_min,
        budget_max=budget_max,
        budget_currency=budget_currency,
        status=OpportunityStatus.SCREENING,
        safety_screening_status=screening.status,
        safety_screening_flags=screening.flags or None,
    )
    db.add(opportunity)
    await db.flush()
    return opportunity


async def list_opportunities(db: AsyncSession, *, tenant_id: uuid.UUID) -> list[Opportunity]:
    result = await db.execute(
        scoped_to_tenant(select(Opportunity), Opportunity, tenant_id).order_by(
            Opportunity.created_at.desc()
        )
    )
    return list(result.scalars().all())


async def get_opportunity(
    db: AsyncSession, *, tenant_id: uuid.UUID, opportunity_id: uuid.UUID
) -> Opportunity | None:
    result = await db.execute(
        scoped_to_tenant(select(Opportunity), Opportunity, tenant_id).where(
            Opportunity.id == opportunity_id
        )
    )
    return result.scalar_one_or_none()


def _confidence_from_missing_info(missing_info: list[str]) -> float:
    """BE7.2: a simple deterministic proxy for confidence -- every piece
    of missing information lowers confidence, floored at 0. Not a
    statistical model (there's no historical data to calibrate one yet),
    just an honest signal that "this result rests on incomplete inputs."
    """
    return round(max(0.0, 1.0 - 0.25 * len(missing_info)), 2)


async def transition_opportunity_status(
    db: AsyncSession, *, opportunity: Opportunity, new_status: OpportunityStatus
) -> Opportunity:
    """BE7.5: the only way `Opportunity.status` should ever change after
    creation -- enforces the pipeline state machine (app/opportunities/
    pipeline.py) so an illegal jump (e.g. `intake` -> `won`) is rejected
    at the service layer, not just hoped to never happen from the UI."""
    if not is_legal_transition(opportunity.status, new_status):
        raise IllegalStatusTransitionError(
            f"Cannot transition from {opportunity.status} to {new_status}."
        )
    opportunity.status = new_status
    await db.flush()
    return opportunity


async def qualify_opportunity_and_persist(
    db: AsyncSession, *, tenant_id: uuid.UUID, created_by: uuid.UUID, opportunity: Opportunity
) -> QualificationResult:
    """BE7.1/BE7.2: scores the opportunity, upserts the single current
    `qualification_results` row for it (ADR 0008), and writes the paired
    explainability record in the same transaction -- a score without its
    "why" is exactly the opaque-output failure mode explainability
    exists to prevent, so these two writes always happen together."""
    if opportunity.safety_screening_status == SafetyScreeningStatus.FLAGGED:
        raise OpportunityFlaggedError(
            "Cannot qualify an opportunity that is still flagged for safety review."
        )

    skills_result = await db.execute(scoped_to_tenant(select(Skill), Skill, tenant_id))
    tenant_skills = list(skills_result.scalars().all())

    score = qualify_opportunity(opportunity=opportunity, tenant_skills=tenant_skills)

    existing = await db.execute(
        scoped_to_tenant(select(QualificationResult), QualificationResult, tenant_id).where(
            QualificationResult.opportunity_id == opportunity.id
        )
    )
    result = existing.scalar_one_or_none()
    if result is None:
        result = QualificationResult(
            tenant_id=tenant_id,
            created_by=created_by,
            opportunity_id=opportunity.id,
            score=score.score,
            reasons=score.reasons,
            evidence=score.evidence,
            missing_info=score.missing_info,
        )
        db.add(result)
    else:
        result.score = score.score
        result.reasons = score.reasons
        result.evidence = score.evidence
        result.missing_info = score.missing_info
    await db.flush()

    await write_explainability_record(
        db,
        tenant_id=tenant_id,
        created_by=created_by,
        entity_type="qualification_result",
        entity_id=result.id,
        decision="qualification_score",
        inputs={
            "budget_min": float(opportunity.budget_min)
            if opportunity.budget_min is not None
            else None,
            "budget_max": float(opportunity.budget_max)
            if opportunity.budget_max is not None
            else None,
            "title": opportunity.title,
            "skills_considered": [s.name for s in tenant_skills],
        },
        evidence=score.evidence,
        rules_applied=["budget_fit", "skill_overlap", "timeline_feasibility"],
        confidence=_confidence_from_missing_info(score.missing_info),
        missing_data=score.missing_info,
    )
    return result


async def match_team_and_persist(
    db: AsyncSession, *, tenant_id: uuid.UUID, created_by: uuid.UUID, opportunity: Opportunity
) -> TeamMatchResult:
    """BE7.3/BE7.2: matches the opportunity against active team members,
    upserts the single current `team_match_results` row (ADR 0008), and
    writes the paired explainability record."""
    skills_result = await db.execute(scoped_to_tenant(select(Skill), Skill, tenant_id))
    tenant_skills = list(skills_result.scalars().all())

    members_result = await db.execute(
        scoped_to_tenant(select(TeamMember), TeamMember, tenant_id).options(
            selectinload(TeamMember.skills)
        )
    )
    team_members = list(members_result.scalars().all())

    match = match_team(
        opportunity=opportunity, tenant_skills=tenant_skills, team_members=team_members
    )

    existing = await db.execute(
        scoped_to_tenant(select(TeamMatchResult), TeamMatchResult, tenant_id).where(
            TeamMatchResult.opportunity_id == opportunity.id
        )
    )
    result = existing.scalar_one_or_none()
    recommended_ids = [str(member_id) for member_id in match.recommended_team_member_ids]
    if result is None:
        result = TeamMatchResult(
            tenant_id=tenant_id,
            created_by=created_by,
            opportunity_id=opportunity.id,
            recommended_team_member_ids=recommended_ids,
            delivery_risk=match.delivery_risk,
            estimated_weekly_cost=match.estimated_weekly_cost,
            estimated_cost_currency=match.estimated_cost_currency,
            gaps=match.gaps,
            reasons=match.reasons,
            evidence=match.evidence,
        )
        db.add(result)
    else:
        result.recommended_team_member_ids = recommended_ids
        result.delivery_risk = match.delivery_risk
        result.estimated_weekly_cost = match.estimated_weekly_cost
        result.estimated_cost_currency = match.estimated_cost_currency
        result.gaps = match.gaps
        result.reasons = match.reasons
        result.evidence = match.evidence
    await db.flush()

    await write_explainability_record(
        db,
        tenant_id=tenant_id,
        created_by=created_by,
        entity_type="team_match_result",
        entity_id=result.id,
        decision="team_match_recommendation",
        inputs={
            "active_team_member_count": sum(1 for m in team_members if m.is_active),
            "skills_considered": [s.name for s in tenant_skills],
        },
        evidence=match.evidence,
        rules_applied=["skill_fit", "delivery_risk_from_coverage_gaps"],
        confidence=1.0 if not match.gaps and match.recommended_team_member_ids else 0.5,
        missing_data=match.gaps,
    )
    return result


async def override_qualification_score(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    result: QualificationResult,
    new_score: int,
    reason: str,
) -> QualificationResult:
    """BE7.6: the only way a human corrects an AI-produced qualification
    score -- never a silent field overwrite. Always records the
    before/after/reason as an `override_records` row first."""
    await write_override_record(
        db,
        tenant_id=tenant_id,
        created_by=actor_id,
        entity_type="qualification_result",
        entity_id=result.id,
        field="score",
        original_value=result.score,
        new_value=new_score,
        reason=reason,
    )
    result.score = new_score
    await db.flush()
    return result


async def override_team_match_selection(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    result: TeamMatchResult,
    new_team_member_ids: list[uuid.UUID],
    reason: str,
) -> TeamMatchResult:
    """BE7.6: the only way a human corrects an AI-recommended team
    selection -- never a silent field overwrite."""
    new_ids = [str(member_id) for member_id in new_team_member_ids]
    await write_override_record(
        db,
        tenant_id=tenant_id,
        created_by=actor_id,
        entity_type="team_match_result",
        entity_id=result.id,
        field="recommended_team_member_ids",
        original_value=result.recommended_team_member_ids,
        new_value=new_ids,
        reason=reason,
    )
    result.recommended_team_member_ids = new_ids
    await db.flush()
    return result


async def get_qualification_result(
    db: AsyncSession, *, tenant_id: uuid.UUID, opportunity_id: uuid.UUID
) -> QualificationResult | None:
    result = await db.execute(
        scoped_to_tenant(select(QualificationResult), QualificationResult, tenant_id).where(
            QualificationResult.opportunity_id == opportunity_id
        )
    )
    return result.scalar_one_or_none()


async def get_team_match_result(
    db: AsyncSession, *, tenant_id: uuid.UUID, opportunity_id: uuid.UUID
) -> TeamMatchResult | None:
    result = await db.execute(
        scoped_to_tenant(select(TeamMatchResult), TeamMatchResult, tenant_id).where(
            TeamMatchResult.opportunity_id == opportunity_id
        )
    )
    return result.scalar_one_or_none()
