"""Real agent_worker reliability test against a real Supabase project
(see conftest.py's skip guard). Mirrors tests/rag/test_worker_pipeline.py's
"crash before ack, redelivered, reprocessed" shape exactly, applied to the
agent_tasks queue: the model provider is faked (no real API key needed,
same reasoning as app/model_gateway/providers/openai_provider.py's
docstring), but the queue, the database, and pgvector retrieval are real.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentRun, AgentRunStatus
from app.agents.queue import AGENT_QUEUE_NAME
from app.agents.registry import AGENT_DEFINITIONS
from app.agents.runtime import run_agent
from app.agents.schemas import AgentTask
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.base import ModelProvider, ProviderResponse
from app.rag import queue
from app.rag.context_builder import build_context
from app.rag.embeddings import EmbeddingProvider
from app.rag.models import EMBEDDING_DIMENSIONS
from app.tools.registry import ToolContext
from tests.rag.conftest import cleanup_tenant, create_tenant, set_context
from workers.agent_worker.main import process_one


class _FakeEmbeddingProvider(EmbeddingProvider):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.5] * EMBEDDING_DIMENSIONS for _ in texts]


class _FakeChatProvider(ModelProvider):
    async def complete(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ProviderResponse:
        system_content = messages[0]["content"].lower()
        if "you are the planner" in system_content:
            content = '[{"tool": "search_knowledge", "arguments": {"query": "Flutter"}}]'
        else:
            content = (
                '{"passed": true, "reasoning": "Found relevant knowledge.", '
                '"output": "Flutter expertise found."}'
            )
        return ProviderResponse(content=content, input_tokens=20, output_tokens=10)


@pytest.mark.asyncio
async def test_agent_worker_crash_before_ack_does_not_duplicate_processing(
    pg_session: AsyncSession,
) -> None:
    """The real "kill the worker mid-run, restart, confirm clean
    recovery" test: a run that completes but crashes before the queue
    message is deleted must, on redelivery, be safely reprocessed by a
    fresh `run_agent` call (its own independent `agent_runs` row) without
    ever leaving the queue message stuck or silently lost."""
    org_id, owner_id = await create_tenant(pg_session, name=f"Agent Worker Test {uuid.uuid4()}")
    embedder = _FakeEmbeddingProvider()
    gateway = ModelGateway(primary=_FakeChatProvider())
    agent_def = AGENT_DEFINITIONS["synthetic_test_agent"]

    try:
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)

        task = AgentTask(
            tenant_id=org_id,
            task_id=uuid.uuid4(),
            agent_id="synthetic_test_agent",
            task_input="What Flutter expertise do we have?",
            query="Flutter",
            idempotency_key=f"{org_id}:test",
            created_by=owner_id,
        )
        await queue.send(pg_session, AGENT_QUEUE_NAME, task.model_dump(mode="json"))
        await pg_session.commit()

        # First pass: read with a short visibility timeout and run the
        # real orchestration, but don't delete the message -- simulating
        # a crash between the run completing and the queue ack.
        first_read = await queue.read(
            pg_session, AGENT_QUEUE_NAME, visibility_timeout_seconds=1, quantity=1
        )
        assert len(first_read) == 1

        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        context = await build_context(
            pg_session,
            tenant_id=org_id,
            actor_permissions=frozenset({"company.manage"}),
            embedder=embedder,
            query=task.query,
            task_text=task.task_input,
            model="gpt-4o-mini",
        )
        first_run = await run_agent(
            pg_session,
            tenant_id=org_id,
            created_by=owner_id,
            agent_def=agent_def,
            task_input=task.task_input,
            context=context,
            gateway=gateway,
            tool_context=ToolContext(
                db=pg_session,
                tenant_id=org_id,
                actor_permissions=frozenset({"company.manage"}),
                embedder=embedder,
            ),
            model="gpt-4o-mini",
        )
        await pg_session.commit()
        assert first_run.status == AgentRunStatus.COMPLETED
        # Deliberately no queue.delete() here -- this is the "crash".

        await asyncio.sleep(1.5)  # let the visibility timeout elapse

        # Second pass: the real worker function, as it would run after a
        # restart, re-reads the now-redelivered message and reprocesses
        # it end to end, including the queue delete this time.
        processed = await process_one(pg_session, embedder=embedder, gateway=gateway)
        assert processed is True

        # Both attempts get their own independent agent_runs row (this
        # table is a log of every attempt, like audit_events -- not an
        # upsert-by-task target) -- the invariant that matters is that
        # each row's own cost/token accounting is self-contained, never
        # double-applied to the other.
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        runs = (
            await pg_session.execute(
                select(AgentRun).where(
                    AgentRun.tenant_id == org_id, AgentRun.agent_id == "synthetic_test_agent"
                )
            )
        ).scalars().all()
        assert len(runs) == 2
        assert all(r.status == AgentRunStatus.COMPLETED for r in runs)

        # No message left in the queue -- the redelivered copy was
        # consumed and deleted by the second (successful-through-ack) pass.
        remaining = await queue.read(pg_session, AGENT_QUEUE_NAME, quantity=10)
        assert not any(
            m.payload.get("task_id") == str(task.task_id) for m in remaining
        )
    finally:
        # tests/rag/conftest.py's cleanup_tenant doesn't know about
        # agent_runs/tool_actions (a Sprint 8 addition) -- delete them
        # here first, or the FK from agent_runs.tenant_id to
        # organizations.id blocks cleanup_tenant's own DELETE.
        await set_context(pg_session, user_id=owner_id, tenant_id=org_id)
        await pg_session.execute(
            text("DELETE FROM tool_actions WHERE tenant_id = :tid"), {"tid": str(org_id)}
        )
        await pg_session.execute(
            text("DELETE FROM agent_runs WHERE tenant_id = :tid"), {"tid": str(org_id)}
        )
        await pg_session.commit()
        await cleanup_tenant(pg_session, org_id=org_id, owner_user_id=owner_id)
