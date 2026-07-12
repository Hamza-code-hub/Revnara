import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.explainability.models import ExplainabilityRecord, OverrideRecord


async def write_explainability_record(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID | None,
    entity_type: str,
    entity_id: uuid.UUID,
    decision: str,
    inputs: dict[str, Any],
    evidence: list[str],
    rules_applied: list[str],
    confidence: float,
    missing_data: list[str],
) -> ExplainabilityRecord:
    """Writes an explainability record as part of the caller's current
    transaction, same commit/rollback semantics as
    app.audit.writer.write_audit_event -- deliberately does not swallow
    exceptions, since a decision without its "why" record is exactly the
    opaque-output failure mode this table exists to prevent.
    """
    record = ExplainabilityRecord(
        tenant_id=tenant_id,
        created_by=created_by,
        entity_type=entity_type,
        entity_id=entity_id,
        decision=decision,
        inputs=inputs,
        evidence=evidence,
        rules_applied=rules_applied,
        confidence=confidence,
        missing_data=missing_data,
    )
    db.add(record)
    await db.flush()
    return record


async def write_override_record(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    field: str,
    original_value: Any,
    new_value: Any,
    reason: str,
) -> OverrideRecord:
    """BE7.6: the only way a human's correction of an AI-produced score
    or team-match selection is ever recorded -- callers must never just
    UPDATE the result row's field directly without also calling this."""
    record = OverrideRecord(
        tenant_id=tenant_id,
        created_by=created_by,
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        original_value=original_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(record)
    await db.flush()
    return record
