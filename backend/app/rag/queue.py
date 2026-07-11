import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class QueueMessage:
    msg_id: int
    read_count: int
    payload: dict[str, Any]


def _is_postgres(db: AsyncSession) -> bool:
    return db.get_bind().dialect.name == "postgresql"


async def create_queue(db: AsyncSession, queue_name: str) -> None:
    """Idempotent -- pgmq.create is a no-op if the queue already exists.
    Requires ownership of the pgmq extension (a provisioning/admin
    operation, like enabling the extension itself) -- the app's regular
    `revnara_app` role can send/read/delete on an already-created queue
    but cannot create a new one; see supabase/config/rag_queues.sql.

    No-op on SQLite (the local test stand-in) -- pgmq doesn't exist there
    at all, the same reason app/tenancy/pg_session.py's session-variable
    functions no-op on SQLite. See docs/rag-pattern.md.
    """
    if not _is_postgres(db):
        return
    await db.execute(text("SELECT pgmq.create(CAST(:name AS text))"), {"name": queue_name})


async def send(db: AsyncSession, queue_name: str, payload: dict[str, Any]) -> int:
    """No-op on SQLite, returning a sentinel -1 -- callers only use the
    returned msg_id for logging, never to look the message back up, so a
    sentinel here doesn't silently break anything on the SQLite path
    (backend/tests/integration/'s CRUD tests exercise the *calling* code,
    e.g. app/files/service.py's confirm_upload, without a real queue)."""
    if not _is_postgres(db):
        return -1
    result = await db.execute(
        text("SELECT pgmq.send(CAST(:name AS text), CAST(:msg AS jsonb)) AS msg_id"),
        {"name": queue_name, "msg": json.dumps(payload, default=str)},
    )
    return int(result.scalar_one())


async def read(
    db: AsyncSession,
    queue_name: str,
    *,
    visibility_timeout_seconds: int = 30,
    quantity: int = 1,
) -> list[QueueMessage]:
    """Reads up to `quantity` messages, each becoming invisible to other
    readers for `visibility_timeout_seconds` -- a message a worker crashes
    while processing simply becomes visible again once that timeout
    elapses, rather than being lost (Sprint 5's "worker crash-and-resume"
    testing task relies on this, combined with the embedding worker's
    upsert-on-conflict idempotency). No-op (empty list) on SQLite."""
    if not _is_postgres(db):
        return []
    result = await db.execute(
        text(
            "SELECT msg_id, read_ct, message FROM pgmq.read("
            "CAST(:name AS text), CAST(:vt AS integer), CAST(:qty AS integer))"
        ),
        {"name": queue_name, "vt": visibility_timeout_seconds, "qty": quantity},
    )
    messages = []
    for row in result.all():
        payload = row.message
        if isinstance(payload, str):
            payload = json.loads(payload)
        messages.append(QueueMessage(msg_id=row.msg_id, read_count=row.read_ct, payload=payload))
    return messages


async def delete(db: AsyncSession, queue_name: str, msg_id: int) -> bool:
    # pgmq.delete is overloaded (single msg_id vs. an array of them) --
    # asyncpg can't resolve which one to call without explicit casts,
    # confirmed by actually calling this against the real Supabase
    # project rather than assuming the signature.
    if not _is_postgres(db):
        return False
    result = await db.execute(
        text("SELECT pgmq.delete(CAST(:name AS text), CAST(:msg_id AS bigint)) AS deleted"),
        {"name": queue_name, "msg_id": msg_id},
    )
    return bool(result.scalar_one())
