import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditEvent, AuditOutcome


async def write_audit_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_type: ActorType,
    actor_id: uuid.UUID,
    action_type: str,
    outcome: AuditOutcome,
    workspace_id: uuid.UUID | None = None,
    error_code: str | None = None,
    **extra_fields: Any,
) -> AuditEvent:
    """Writes an audit event as part of the caller's current transaction.

    Deliberately does NOT catch exceptions -- per
    docs/BDOS_Enforcement_Spec.md Core Rule #12 ("audit recording succeeds
    or the action fails closed"), a failure here must propagate and roll
    back the whole request (handled by app.database.get_db_session's
    commit/rollback wrapper), never be logged-and-ignored while the
    mutating action it's meant to record still goes through.
    """
    event = AuditEvent(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action_type=action_type,
        outcome=outcome,
        error_code=error_code,
        **extra_fields,
    )
    db.add(event)
    await db.flush()  # surfaces any failure now, not just at final commit
    return event
