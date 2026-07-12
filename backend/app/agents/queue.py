from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import AgentTask

# app.rag.queue is a generic pgmq wrapper despite its module path (no
# RAG-specific logic in it at all) -- reused directly here rather than
# duplicated, see its own docstrings for the SQLite-no-op/asyncpg-cast
# gotchas that already apply identically to this queue.
from app.rag.queue import send

AGENT_QUEUE_NAME = "agent_tasks"


async def enqueue_agent_task(db: AsyncSession, task: AgentTask) -> int:
    return await send(db, AGENT_QUEUE_NAME, task.model_dump(mode="json"))
