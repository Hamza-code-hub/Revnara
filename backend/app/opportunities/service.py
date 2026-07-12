import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.opportunities.models import (
    Client,
    Opportunity,
    OpportunitySource,
    OpportunitySourceType,
    OpportunityStatus,
)
from app.opportunities.safety_screening import screen_opportunity
from app.tenancy.repository import scoped_to_tenant


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
