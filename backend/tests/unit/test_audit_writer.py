import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event


@pytest.mark.asyncio
async def test_write_audit_event_persists_the_row(db_session: AsyncSession) -> None:
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    event = await write_audit_event(
        db_session,
        tenant_id=tenant_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action_type="test.action",
        outcome=AuditOutcome.EXECUTED,
    )

    assert event.id is not None
    assert event.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_audit_write_failure_propagates_instead_of_being_swallowed(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enforcement Spec test requirement #9 / Core Rule #12: audit
    recording succeeds or the action fails closed. write_audit_event must
    never catch and log-and-continue on a DB failure -- the exception has
    to reach the caller (and, in a real request, app.database.get_db_session's
    rollback), or a failed audit write would silently let the action it
    was supposed to record go through unrecorded.
    """

    async def failing_flush() -> None:
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(db_session, "flush", failing_flush)

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        await write_audit_event(
            db_session,
            tenant_id=uuid.uuid4(),
            actor_type=ActorType.USER,
            actor_id=uuid.uuid4(),
            action_type="test.action",
            outcome=AuditOutcome.EXECUTED,
        )
