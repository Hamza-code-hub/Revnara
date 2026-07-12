import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
from app.database import get_db_session
from app.explainability.reader import get_latest_explainability_record, list_override_records
from app.explainability.schemas import ExplainabilityRecordRead, OverrideRecordRead
from app.opportunities import service
from app.opportunities.csv_import import parse_opportunities_csv
from app.opportunities.models import Client, Opportunity, OpportunitySourceType
from app.opportunities.research import generate_research_brief
from app.opportunities.schemas import (
    ClientRead,
    CsvImportResult,
    CsvImportRowError,
    OpportunityCreate,
    OpportunityImportLinkCreate,
    OpportunityRead,
    OpportunityStatusUpdate,
    QualificationOverride,
    QualificationResultRead,
    TeamMatchOverride,
    TeamMatchResultRead,
)
from app.opportunities.service import IllegalStatusTransitionError, OpportunityFlaggedError
from app.organizations.authorization import require_permission
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context
from app.tenancy.repository import scoped_to_tenant

router = APIRouter(tags=["opportunities"])


def _check_tenant(organization_id: uuid.UUID, tenant: TenantContext) -> None:
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")


@router.get("/organizations/{organization_id}/opportunities", response_model=list[OpportunityRead])
async def list_opportunities(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[OpportunityRead]:
    _check_tenant(organization_id, tenant)
    opportunities = await service.list_opportunities(db, tenant_id=organization_id)
    return [OpportunityRead.model_validate(o) for o in opportunities]


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}",
    response_model=OpportunityRead,
)
async def get_opportunity(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> OpportunityRead:
    _check_tenant(organization_id, tenant)
    opportunity = await service.get_opportunity(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    return OpportunityRead.model_validate(opportunity)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/client",
    response_model=ClientRead,
)
async def get_opportunity_client(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> ClientRead:
    """Generates (and persists) BE6.5b's deterministic research brief on
    first request if the client doesn't have one yet, rather than at
    creation time -- so relevant opportunity history up to *this exact
    moment* is reflected, not just what existed when the client row was
    first created."""
    _check_tenant(organization_id, tenant)
    opportunity = await service.get_opportunity(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if opportunity is None or opportunity.client_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    result = await db.execute(
        scoped_to_tenant(select(Client), Client, organization_id).where(
            Client.id == opportunity.client_id
        )
    )
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    if client.research_brief is None:
        client.research_brief = await generate_research_brief(
            db, tenant_id=organization_id, client=client
        )
        client.research_generated_at = datetime.now(UTC)
        await db.flush()

    return ClientRead.model_validate(client)


@router.post(
    "/organizations/{organization_id}/opportunities",
    response_model=OpportunityRead,
    status_code=201,
)
async def create_opportunity(
    organization_id: uuid.UUID,
    payload: OpportunityCreate,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> OpportunityRead:
    _check_tenant(organization_id, tenant)
    opportunity = await service.create_opportunity(
        db,
        tenant_id=organization_id,
        created_by=tenant.user_id,
        source_type=OpportunitySourceType.MANUAL,
        title=payload.title,
        description=payload.description,
        requirements=payload.requirements,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        budget_currency=payload.budget_currency,
        client_name=payload.client_name,
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.create",
        outcome=AuditOutcome.EXECUTED,
    )
    return OpportunityRead.model_validate(opportunity)


@router.post(
    "/organizations/{organization_id}/opportunities/import-link",
    response_model=OpportunityRead,
    status_code=201,
)
async def import_opportunity_link(
    organization_id: uuid.UUID,
    payload: OpportunityImportLinkCreate,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> OpportunityRead:
    """FE6.3/BE6.2: stores the pasted link + metadata only. This handler
    (and everything it calls) never makes a network request to Upwork or
    any other platform -- verified by
    tests/security/test_no_upwork_automation.py's negative test."""
    _check_tenant(organization_id, tenant)
    opportunity = await service.create_opportunity(
        db,
        tenant_id=organization_id,
        created_by=tenant.user_id,
        source_type=OpportunitySourceType.UPWORK_LINK,
        title=payload.title,
        description=payload.description,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        budget_currency=payload.budget_currency,
        client_name=payload.client_name,
        external_url=payload.url,
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.import_link",
        outcome=AuditOutcome.EXECUTED,
    )
    return OpportunityRead.model_validate(opportunity)


@router.post(
    "/organizations/{organization_id}/opportunities/import",
    response_model=CsvImportResult,
    status_code=201,
)
async def import_opportunities_csv(
    organization_id: uuid.UUID,
    file: UploadFile,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> CsvImportResult:
    _check_tenant(organization_id, tenant)

    raw_bytes = await file.read()
    content = raw_bytes.decode("utf-8", errors="replace")
    parse_result = parse_opportunities_csv(content)

    created = []
    for row in parse_result.rows:
        opportunity = await service.create_opportunity(
            db,
            tenant_id=organization_id,
            created_by=tenant.user_id,
            source_type=OpportunitySourceType.CSV_IMPORT,
            title=row.title,
            description=row.description,
            requirements=row.requirements,
            budget_min=row.budget_min,
            budget_max=row.budget_max,
            budget_currency=row.budget_currency,
            client_name=row.client_name,
            raw_metadata={"row_number": row.row_number},
        )
        created.append(opportunity)

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.import_csv",
        outcome=AuditOutcome.EXECUTED,
    )

    return CsvImportResult(
        created=[OpportunityRead.model_validate(o) for o in created],
        errors=[
            CsvImportRowError(row_number=e.row_number, error=e.error) for e in parse_result.errors
        ],
    )


async def _get_opportunity_or_404(
    db: AsyncSession, *, organization_id: uuid.UUID, opportunity_id: uuid.UUID
) -> Opportunity:
    opportunity = await service.get_opportunity(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    return opportunity


@router.patch(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/status",
    response_model=OpportunityRead,
)
async def update_opportunity_status(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    payload: OpportunityStatusUpdate,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> OpportunityRead:
    """BE7.5: the pipeline state machine -- illegal jumps (e.g. `intake`
    -> `won`) are rejected here, not just discouraged in the UI."""
    _check_tenant(organization_id, tenant)
    opportunity = await _get_opportunity_or_404(
        db, organization_id=organization_id, opportunity_id=opportunity_id
    )
    try:
        opportunity = await service.transition_opportunity_status(
            db, opportunity=opportunity, new_status=payload.status
        )
    except IllegalStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.status_change",
        outcome=AuditOutcome.EXECUTED,
    )
    return OpportunityRead.model_validate(opportunity)


@router.post(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/qualify",
    response_model=QualificationResultRead,
)
async def qualify_opportunity(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> QualificationResultRead:
    _check_tenant(organization_id, tenant)
    opportunity = await _get_opportunity_or_404(
        db, organization_id=organization_id, opportunity_id=opportunity_id
    )
    try:
        result = await service.qualify_opportunity_and_persist(
            db, tenant_id=organization_id, created_by=tenant.user_id, opportunity=opportunity
        )
    except OpportunityFlaggedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.qualify",
        outcome=AuditOutcome.EXECUTED,
    )
    return QualificationResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/qualification",
    response_model=QualificationResultRead,
)
async def get_qualification_result(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> QualificationResultRead:
    _check_tenant(organization_id, tenant)
    result = await service.get_qualification_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No qualification result yet."
        )
    return QualificationResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/qualification/explainability",
    response_model=ExplainabilityRecordRead,
)
async def get_qualification_explainability(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> ExplainabilityRecordRead:
    _check_tenant(organization_id, tenant)
    result = await service.get_qualification_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No qualification result yet."
        )
    record = await get_latest_explainability_record(
        db, tenant_id=organization_id, entity_type="qualification_result", entity_id=result.id
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No explanation yet.")
    return ExplainabilityRecordRead.model_validate(record)


@router.patch(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/qualification",
    response_model=QualificationResultRead,
)
async def override_qualification(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    payload: QualificationOverride,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> QualificationResultRead:
    """BE7.6: a human correcting the AI-produced score -- always recorded
    as an `override_records` row (payload.reason is required), never a
    bare field edit."""
    _check_tenant(organization_id, tenant)
    result = await service.get_qualification_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No qualification result yet."
        )
    result = await service.override_qualification_score(
        db,
        tenant_id=organization_id,
        actor_id=tenant.user_id,
        result=result,
        new_score=payload.score,
        reason=payload.reason,
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.qualification.override",
        outcome=AuditOutcome.EXECUTED,
    )
    return QualificationResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/qualification/overrides",
    response_model=list[OverrideRecordRead],
)
async def list_qualification_overrides(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[OverrideRecordRead]:
    _check_tenant(organization_id, tenant)
    result = await service.get_qualification_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No qualification result yet."
        )
    overrides = await list_override_records(
        db, tenant_id=organization_id, entity_type="qualification_result", entity_id=result.id
    )
    return [OverrideRecordRead.model_validate(o) for o in overrides]


@router.post(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/match-team",
    response_model=TeamMatchResultRead,
)
async def match_team_for_opportunity(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> TeamMatchResultRead:
    _check_tenant(organization_id, tenant)
    opportunity = await _get_opportunity_or_404(
        db, organization_id=organization_id, opportunity_id=opportunity_id
    )
    result = await service.match_team_and_persist(
        db, tenant_id=organization_id, created_by=tenant.user_id, opportunity=opportunity
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.match_team",
        outcome=AuditOutcome.EXECUTED,
    )
    return TeamMatchResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/team-match",
    response_model=TeamMatchResultRead,
)
async def get_team_match_result(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> TeamMatchResultRead:
    _check_tenant(organization_id, tenant)
    result = await service.get_team_match_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team match yet.")
    return TeamMatchResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/team-match/explainability",
    response_model=ExplainabilityRecordRead,
)
async def get_team_match_explainability(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> ExplainabilityRecordRead:
    _check_tenant(organization_id, tenant)
    result = await service.get_team_match_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team match yet.")
    record = await get_latest_explainability_record(
        db, tenant_id=organization_id, entity_type="team_match_result", entity_id=result.id
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No explanation yet.")
    return ExplainabilityRecordRead.model_validate(record)


@router.patch(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/team-match",
    response_model=TeamMatchResultRead,
)
async def override_team_match(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    payload: TeamMatchOverride,
    tenant: TenantContext = Depends(require_permission("opportunities.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> TeamMatchResultRead:
    """BE7.6: a human correcting the AI-recommended team selection --
    always recorded as an `override_records` row, never a bare field
    edit."""
    _check_tenant(organization_id, tenant)
    result = await service.get_team_match_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team match yet.")
    result = await service.override_team_match_selection(
        db,
        tenant_id=organization_id,
        actor_id=tenant.user_id,
        result=result,
        new_team_member_ids=payload.recommended_team_member_ids,
        reason=payload.reason,
    )

    await write_audit_event(
        db,
        tenant_id=organization_id,
        actor_type=ActorType.USER,
        actor_id=tenant.user_id,
        action_type="opportunity.team_match.override",
        outcome=AuditOutcome.EXECUTED,
    )
    return TeamMatchResultRead.model_validate(result)


@router.get(
    "/organizations/{organization_id}/opportunities/{opportunity_id}/team-match/overrides",
    response_model=list[OverrideRecordRead],
)
async def list_team_match_overrides(
    organization_id: uuid.UUID,
    opportunity_id: uuid.UUID,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
) -> list[OverrideRecordRead]:
    _check_tenant(organization_id, tenant)
    result = await service.get_team_match_result(
        db, tenant_id=organization_id, opportunity_id=opportunity_id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team match yet.")
    overrides = await list_override_records(
        db, tenant_id=organization_id, entity_type="team_match_result", entity_id=result.id
    )
    return [OverrideRecordRead.model_validate(o) for o in overrides]
