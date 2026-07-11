"""Real pgmq round-trip tests against a real Supabase project (see
conftest.py's skip guard). Uses the already-provisioned `document_tasks`
queue (supabase/config/rag_queues.sql) rather than creating a throwaway
one, since queue creation itself requires extension-owner privilege the
app's own `revnara_app` role deliberately doesn't have -- see
docs/rag-pattern.md.
"""

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import queue

_QUEUE_NAME = "document_tasks"


@pytest.mark.asyncio
async def test_send_read_delete_round_trip(pg_session: AsyncSession) -> None:
    marker = str(uuid.uuid4())
    msg_id = await queue.send(pg_session, _QUEUE_NAME, {"marker": marker})
    await pg_session.commit()

    messages = await queue.read(pg_session, _QUEUE_NAME, quantity=10)
    await pg_session.commit()
    matching = [m for m in messages if m.payload.get("marker") == marker]
    assert len(matching) == 1
    assert matching[0].msg_id == msg_id

    deleted = await queue.delete(pg_session, _QUEUE_NAME, msg_id)
    await pg_session.commit()
    assert deleted is True

    # Deleting again (already gone) returns False, not an error.
    deleted_again = await queue.delete(pg_session, _QUEUE_NAME, msg_id)
    await pg_session.commit()
    assert deleted_again is False


@pytest.mark.asyncio
async def test_message_becomes_visible_again_after_visibility_timeout_elapses(
    pg_session: AsyncSession,
) -> None:
    """Proves pgmq's redelivery mechanism for real -- a message that's
    read but never deleted (the "worker crashed before acking" scenario)
    reappears once its visibility timeout elapses, rather than being lost.
    This is half of what makes Sprint 5's "worker crash-and-resume, no
    lost tasks" testing requirement true (see test_worker_pipeline.py for
    the other half: the embedding upsert not duplicating on redelivery).
    """
    marker = str(uuid.uuid4())
    msg_id = await queue.send(pg_session, _QUEUE_NAME, {"marker": marker})
    await pg_session.commit()

    first_read = await queue.read(
        pg_session, _QUEUE_NAME, visibility_timeout_seconds=1, quantity=10
    )
    await pg_session.commit()
    assert any(m.msg_id == msg_id for m in first_read)

    # Still invisible immediately after the first read -- a second reader
    # (or the same worker looping too fast) must not see it yet.
    immediate_reread = await queue.read(pg_session, _QUEUE_NAME, quantity=10)
    await pg_session.commit()
    assert not any(m.msg_id == msg_id for m in immediate_reread)

    await asyncio.sleep(1.5)

    reread_after_timeout = await queue.read(pg_session, _QUEUE_NAME, quantity=10)
    await pg_session.commit()
    assert any(m.msg_id == msg_id for m in reread_after_timeout)

    await queue.delete(pg_session, _QUEUE_NAME, msg_id)
    await pg_session.commit()
