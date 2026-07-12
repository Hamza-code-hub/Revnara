import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentDefinition, AgentLimits
from app.agents.models import AgentRun, AgentRunStatus, ToolAction
from app.agents.runtime import run_agent
from app.audit.models import AuditEvent, AuditOutcome
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.base import ModelProvider, ProviderResponse
from app.tools import registry as tools_registry
from app.tools.registry import ToolContext, ToolDefinition


class _SequencedFakeProvider(ModelProvider):
    """Distinguishes the planner call from the verifier call by
    inspecting the system prompt content -- app/agents/planner.py's and
    verifier.py's system prompts are each distinctly labeled, exactly as
    real callers would use them."""

    def __init__(self, *, plan_content: str, verification_content: str) -> None:
        self._plan_content = plan_content
        self._verification_content = verification_content

    async def complete(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ProviderResponse:
        system_content = messages[0]["content"].lower()
        if "you are the planner" in system_content:
            return ProviderResponse(
                content=self._plan_content, input_tokens=50, output_tokens=20
            )
        return ProviderResponse(
            content=self._verification_content, input_tokens=30, output_tokens=15
        )


async def _echo_tool_handler(ctx: ToolContext, arguments: dict) -> dict:
    return {"echoed": arguments.get("text", "")}


@pytest.fixture
def echo_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registers a trivial DB-independent tool for the duration of one
    test -- the registry's real `search_knowledge` needs pgvector (a real
    Postgres project, tested separately in tests/agents/), but the
    orchestration logic itself (planner -> executor -> verifier, limits,
    allowlist enforcement) doesn't depend on any specific tool's
    internals and is exercised faster and just as validly against a
    trivial stand-in."""
    monkeypatch.setitem(
        tools_registry.TOOL_REGISTRY,
        "echo_tool",
        ToolDefinition(
            name="echo_tool", description="Echoes text back.", handler=_echo_tool_handler
        ),
    )


def _agent_def(**overrides: object) -> AgentDefinition:
    defaults: dict[str, object] = {
        "id": "test_agent",
        "version": "1.0.0",
        "owner": "platform",
        "purpose": "test purpose",
        "input_description": "test",
        "output_description": "test",
        "allowed_tools": ["echo_tool"],
        "prohibited_tools": [],
        "limits": AgentLimits(
            max_tool_calls=5, max_runtime_seconds=30, max_tokens=10_000, max_cost_usd=1.0
        ),
    }
    defaults.update(overrides)
    return AgentDefinition(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_full_round_trip_produces_completed_run_with_tool_action(
    db_session: AsyncSession, echo_tool: None
) -> None:
    provider = _SequencedFakeProvider(
        plan_content='[{"tool": "echo_tool", "arguments": {"text": "hello"}}]',
        verification_content='{"passed": true, "reasoning": "Echo worked.", "output": "hello"}',
    )
    gateway = ModelGateway(primary=provider)
    tenant_id = uuid.uuid4()

    run = await run_agent(
        db_session,
        tenant_id=tenant_id,
        created_by=None,
        agent_def=_agent_def(),
        task_input="Please echo hello.",
        context="(no context needed for this test)",
        gateway=gateway,
        tool_context=ToolContext(
            db=db_session, tenant_id=tenant_id, actor_permissions=frozenset(), embedder=None  # type: ignore[arg-type]
        ),
        model="gpt-4o-mini",
    )

    assert run.status == AgentRunStatus.COMPLETED
    assert run.outputs is not None
    assert run.outputs["output"] == "hello"
    assert run.tool_call_count == 1
    assert run.total_input_tokens == 80
    assert run.total_output_tokens == 35
    assert run.total_cost_usd > 0

    persisted_run = (
        await db_session.execute(select(AgentRun).where(AgentRun.id == run.id))
    ).scalar_one()
    assert persisted_run.status == AgentRunStatus.COMPLETED

    tool_actions = (
        await db_session.execute(select(ToolAction).where(ToolAction.agent_run_id == run.id))
    ).scalars().all()
    assert len(tool_actions) == 1
    assert tool_actions[0].was_allowed is True
    assert tool_actions[0].result == {"echoed": "hello"}


@pytest.mark.asyncio
async def test_disallowed_tool_call_is_blocked_and_audited(
    db_session: AsyncSession, echo_tool: None
) -> None:
    provider = _SequencedFakeProvider(
        plan_content='[{"tool": "some_other_tool", "arguments": {}}]',
        verification_content='{"passed": false, "reasoning": "Tool was blocked.", "output": ""}',
    )
    gateway = ModelGateway(primary=provider)
    tenant_id = uuid.uuid4()

    run = await run_agent(
        db_session,
        tenant_id=tenant_id,
        created_by=None,
        agent_def=_agent_def(allowed_tools=["echo_tool"]),
        task_input="Try something not allowed.",
        context="",
        gateway=gateway,
        tool_context=ToolContext(
            db=db_session, tenant_id=tenant_id, actor_permissions=frozenset(), embedder=None  # type: ignore[arg-type]
        ),
        model="gpt-4o-mini",
    )

    tool_actions = (
        await db_session.execute(select(ToolAction).where(ToolAction.agent_run_id == run.id))
    ).scalars().all()
    assert len(tool_actions) == 1
    assert tool_actions[0].was_allowed is False
    assert tool_actions[0].tool_name == "some_other_tool"

    audit_events = (
        await db_session.execute(
            select(AuditEvent).where(AuditEvent.action_type == "agent.tool_call.blocked")
        )
    ).scalars().all()
    assert len(audit_events) == 1
    assert audit_events[0].outcome == AuditOutcome.BLOCKED
    assert audit_events[0].actor_id == run.id


@pytest.mark.asyncio
async def test_exceeding_max_tool_calls_halts_run_cleanly(
    db_session: AsyncSession, echo_tool: None
) -> None:
    provider = _SequencedFakeProvider(
        plan_content=(
            '[{"tool": "echo_tool", "arguments": {"text": "one"}}, '
            '{"tool": "echo_tool", "arguments": {"text": "two"}}]'
        ),
        verification_content='{"passed": true, "reasoning": "n/a", "output": "n/a"}',
    )
    gateway = ModelGateway(primary=provider)
    tenant_id = uuid.uuid4()

    run = await run_agent(
        db_session,
        tenant_id=tenant_id,
        created_by=None,
        agent_def=_agent_def(
            allowed_tools=["echo_tool"],
            limits=AgentLimits(
                max_tool_calls=1, max_runtime_seconds=30, max_tokens=10_000, max_cost_usd=1.0
            ),
        ),
        task_input="Do two things.",
        context="",
        gateway=gateway,
        tool_context=ToolContext(
            db=db_session, tenant_id=tenant_id, actor_permissions=frozenset(), embedder=None  # type: ignore[arg-type]
        ),
        model="gpt-4o-mini",
    )

    assert run.status == AgentRunStatus.HALTED
    assert run.halt_reason is not None
    assert "max_tool_calls" in run.halt_reason

    # The first tool call still completed and was persisted -- a halt
    # doesn't discard already-completed work.
    tool_actions = (
        await db_session.execute(select(ToolAction).where(ToolAction.agent_run_id == run.id))
    ).scalars().all()
    assert len(tool_actions) == 1


@pytest.mark.asyncio
async def test_exceeding_max_cost_halts_run_cleanly(
    db_session: AsyncSession, echo_tool: None
) -> None:
    provider = _SequencedFakeProvider(
        plan_content='[{"tool": "echo_tool", "arguments": {"text": "hi"}}]',
        verification_content='{"passed": true, "reasoning": "n/a", "output": "n/a"}',
    )
    gateway = ModelGateway(primary=provider)
    tenant_id = uuid.uuid4()

    run = await run_agent(
        db_session,
        tenant_id=tenant_id,
        created_by=None,
        agent_def=_agent_def(
            allowed_tools=["echo_tool"],
            limits=AgentLimits(
                max_tool_calls=5, max_runtime_seconds=30, max_tokens=10_000, max_cost_usd=0.0
            ),
        ),
        task_input="Do one thing.",
        context="",
        gateway=gateway,
        tool_context=ToolContext(
            db=db_session, tenant_id=tenant_id, actor_permissions=frozenset(), embedder=None  # type: ignore[arg-type]
        ),
        model="gpt-4o-mini",
    )

    assert run.status == AgentRunStatus.HALTED
    assert run.halt_reason is not None
    assert "max_cost_usd" in run.halt_reason
