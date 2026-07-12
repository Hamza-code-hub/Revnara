import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.queue import AGENT_QUEUE_NAME
from app.agents.registry import get_agent_definition
from app.agents.runtime import run_agent
from app.agents.schemas import AgentTask
from app.config import get_settings
from app.database import session_factory
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.openai_provider import OpenAIChatProvider
from app.rag import queue
from app.rag.context_builder import build_context
from app.rag.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from app.tenancy.pg_session import set_pg_tenant_context
from app.tools.registry import ToolContext

logger = logging.getLogger(__name__)

_VISIBILITY_TIMEOUT_SECONDS = 90
_IDLE_POLL_SECONDS = 5
_MODEL = "gpt-4o-mini"

# A background agent run isn't acting on behalf of one specific human
# member with their own narrower grants -- it gets the tenant's own full
# read access, still classification-filtered by retrieval.search the
# same as any caller (company.manage is what unlocks confidential rows).
_WORKER_PERMISSIONS = frozenset({"company.manage"})


async def process_one(
    db: AsyncSession,
    *,
    embedder: EmbeddingProvider,
    gateway: ModelGateway,
) -> bool:
    """Reads and processes a single agent_task. Returns False if the
    queue was empty. BE8's worker-reliability requirement ("crash
    mid-run does not double-charge cost or double-write results") holds
    because a redelivered message (pgmq's visibility timeout, not
    deletion) simply causes `run_agent` to create a brand new
    `agent_runs` row for the retry -- the original attempt's row (and
    whatever partial cost/tokens it already accumulated before the
    crash) is untouched, not re-applied to or merged with anything."""
    messages = await queue.read(
        db, AGENT_QUEUE_NAME, visibility_timeout_seconds=_VISIBILITY_TIMEOUT_SECONDS, quantity=1
    )
    if not messages:
        return False

    message = messages[0]
    task = AgentTask.model_validate(message.payload)

    # Same reason as document_worker/embedding_worker: a worker session
    # has no single "current tenant" the way a request's does, and RLS
    # applies to every write on this connection regardless.
    await set_pg_tenant_context(db, task.tenant_id)

    agent_def = get_agent_definition(task.agent_id)

    context = await build_context(
        db,
        tenant_id=task.tenant_id,
        actor_permissions=_WORKER_PERMISSIONS,
        embedder=embedder,
        query=task.query,
        task_text=task.task_input,
        model=_MODEL,
    )

    tool_context = ToolContext(
        db=db,
        tenant_id=task.tenant_id,
        actor_permissions=_WORKER_PERMISSIONS,
        embedder=embedder,
    )

    run = await run_agent(
        db,
        tenant_id=task.tenant_id,
        created_by=task.created_by,
        agent_def=agent_def,
        task_input=task.task_input,
        context=context,
        gateway=gateway,
        tool_context=tool_context,
        model=_MODEL,
    )
    logger.info(
        "agent_worker: run %s for agent %s finished as %s", run.id, task.agent_id, run.status
    )

    await queue.delete(db, AGENT_QUEUE_NAME, message.msg_id)
    await db.commit()
    return True


async def run_forever() -> None:
    settings = get_settings()
    embedder = OpenAIEmbeddingProvider(api_key=settings.model_provider_api_key)
    primary = OpenAIChatProvider(api_key=settings.model_provider_api_key)
    fallback = (
        OpenAIChatProvider(api_key=settings.model_provider_fallback_api_key)
        if settings.model_provider_fallback_api_key
        else None
    )
    gateway = ModelGateway(primary=primary, fallback=fallback)

    while True:
        async with session_factory() as db:
            try:
                processed = await process_one(db, embedder=embedder, gateway=gateway)
            except Exception:
                logger.exception("agent_worker: error processing task")
                await db.rollback()
                processed = True
        if not processed:
            await asyncio.sleep(_IDLE_POLL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
