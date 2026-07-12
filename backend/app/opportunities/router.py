import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
from app.database import get_db_session
from app.opportunities import service
from app.opportunities.csv_import import parse_opportunities_csv
from app.opportunities.models import Client, OpportunitySourceType
from app.opportunities.research import generate_research_brief
from app.opportunities.schemas import (
    ClientRead,
    CsvImportResult,
    CsvImportRowError,
    OpportunityCreate,
    OpportunityImportLinkCreate,
    OpportunityRead,
)
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
