import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.explainability.models import ExplainabilityRecord, OverrideRecord
from app.tenancy.repository import scoped_to_tenant


async def get_latest_explainability_record(
    db: AsyncSession, *, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID
) -> ExplainabilityRecord | None:
    """Explainability records are never updated in place (RLS forbids it
    -- see supabase/rls/explainability_records.sql), so "the current why"
    for an entity is its most recent record, not its only one."""
    result = await db.execute(
        scoped_to_tenant(select(ExplainabilityRecord), ExplainabilityRecord, tenant_id)
        .where(
            ExplainabilityRecord.entity_type == entity_type,
            ExplainabilityRecord.entity_id == entity_id,
        )
        .order_by(ExplainabilityRecord.created_at.desc())
    )
    return result.scalars().first()


async def list_override_records(
    db: AsyncSession, *, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID
) -> list[OverrideRecord]:
    """FE7.2b: every correction ever made to this entity, most recent
    first -- what the opportunity detail view's "adjusted by [person]"
    indicator reads from."""
    result = await db.execute(
        scoped_to_tenant(select(OverrideRecord), OverrideRecord, tenant_id)
        .where(
            OverrideRecord.entity_type == entity_type,
            OverrideRecord.entity_id == entity_id,
        )
        .order_by(OverrideRecord.created_at.desc())
    )
    return list(result.scalars().all())
