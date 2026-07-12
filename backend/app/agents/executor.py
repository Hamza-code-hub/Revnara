import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentDefinition
from app.agents.models import ToolAction
from app.agents.registry import is_tool_allowed
from app.audit.models import ActorType, AuditOutcome
from app.audit.writer import write_audit_event
from app.tools.registry import ToolContext, UnknownToolError, invoke_tool
from app.tools.schemas import ToolCall


class AgentRunLimitExceededError(Exception):
    """BE8: a run's own limits (max_tool_calls here) were exceeded --
    caught by the orchestrator, which halts the run cleanly with this
    reason recorded rather than letting it run unbounded."""


@dataclass(frozen=True)
class ExecutionOutcome:
    tool_actions: list[ToolAction]


async def execute_plan(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    agent_def: AgentDefinition,
    plan: list[ToolCall],
    tool_context: ToolContext,
) -> ExecutionOutcome:
    """BE8.4/BE8.5: executes each planned tool call, enforcing the
    agent's allowlist independently of whatever the planner's model
    output claimed -- the model's own restraint is never trusted as the
    only gate. Every attempt (allowed or blocked) becomes a `ToolAction`
    row; a blocked attempt also writes an audit event, since this is the
    first real enforcement point for Blueprint §6.3's "no agent
    self-authorization" principle.
    """
    tool_actions: list[ToolAction] = []

    for call in plan:
        if len(tool_actions) >= agent_def.limits.max_tool_calls:
            raise AgentRunLimitExceededError(
                f"max_tool_calls ({agent_def.limits.max_tool_calls}) exceeded"
            )

        allowed = is_tool_allowed(agent_def, call.tool)
        result = None
        error = None

        if not allowed:
            error = "Tool not in this agent's allowlist."
            await write_audit_event(
                db,
                tenant_id=tenant_id,
                actor_type=ActorType.AGENT,
                actor_id=agent_run_id,
                action_type="agent.tool_call.blocked",
                outcome=AuditOutcome.BLOCKED,
            )
        else:
            try:
                result = await invoke_tool(
                    tool_name=call.tool,
                    allowed_tools=agent_def.allowed_tools,
                    prohibited_tools=agent_def.prohibited_tools,
                    context=tool_context,
                    arguments=call.arguments,
                )
            except UnknownToolError as exc:
                error = str(exc)

        action = ToolAction(
            tenant_id=tenant_id,
            agent_run_id=agent_run_id,
            tool_name=call.tool,
            arguments=call.arguments,
            result=result,
            was_allowed=allowed,
            error=error,
        )
        db.add(action)
        await db.flush()
        tool_actions.append(action)

    return ExecutionOutcome(tool_actions=tool_actions)
