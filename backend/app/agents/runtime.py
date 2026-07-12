import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentDefinition
from app.agents.executor import AgentRunLimitExceededError, execute_plan
from app.agents.models import AgentRun, AgentRunStatus
from app.agents.planner import create_plan
from app.agents.verifier import verify_results
from app.model_gateway.gateway import ModelGateway, ModelProviderError
from app.tools.registry import ToolContext


class AgentRunHaltedError(Exception):
    """A configured limit was hit -- the run stops on purpose, cleanly,
    with a recorded reason (AgentRun.halt_reason), not a crash."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


async def run_agent(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by: uuid.UUID | None,
    agent_def: AgentDefinition,
    task_input: str,
    context: str,
    gateway: ModelGateway,
    tool_context: ToolContext,
    model: str,
) -> AgentRun:
    """BE8.5/BE8.7: the planner -> executor -> verifier orchestration
    every agent run goes through. The `agent_runs` row is created and
    flushed up front, so even a run that crashes mid-way has a
    persisted record -- and the agent's max_runtime_seconds/max_tokens/
    max_cost_usd limits are checked after every step, halting cleanly
    (status=halted, with a reason) rather than running unbounded or
    raising an uncaught exception.
    """
    run = AgentRun(
        tenant_id=tenant_id,
        created_by=created_by,
        agent_id=agent_def.id,
        agent_version=agent_def.version,
        status=AgentRunStatus.RUNNING,
        inputs={"task_input": task_input},
        total_input_tokens=0,
        total_output_tokens=0,
        total_cost_usd=0.0,
        tool_call_count=0,
    )
    db.add(run)
    await db.flush()

    started_at = run.started_at

    def _elapsed_seconds() -> float:
        return (datetime.now(UTC) - started_at).total_seconds()

    def _accumulate(input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        run.total_input_tokens += input_tokens
        run.total_output_tokens += output_tokens
        run.total_cost_usd = float(run.total_cost_usd) + cost_usd

    def _check_limits() -> str | None:
        if _elapsed_seconds() > agent_def.limits.max_runtime_seconds:
            return f"max_runtime_seconds ({agent_def.limits.max_runtime_seconds}) exceeded"
        total_tokens = run.total_input_tokens + run.total_output_tokens
        if total_tokens > agent_def.limits.max_tokens:
            return f"max_tokens ({agent_def.limits.max_tokens}) exceeded"
        if float(run.total_cost_usd) > agent_def.limits.max_cost_usd:
            return f"max_cost_usd ({agent_def.limits.max_cost_usd}) exceeded"
        return None

    try:
        plan, plan_in, plan_out, plan_cost = await create_plan(
            gateway=gateway,
            agent_def=agent_def,
            task_input=task_input,
            context=context,
            model=model,
        )
        _accumulate(plan_in, plan_out, plan_cost)
        halt_reason = _check_limits()
        if halt_reason:
            raise AgentRunHaltedError(halt_reason)

        execution = await execute_plan(
            db,
            tenant_id=tenant_id,
            agent_run_id=run.id,
            agent_def=agent_def,
            plan=plan,
            tool_context=tool_context,
        )
        run.tool_call_count = len(execution.tool_actions)
        halt_reason = _check_limits()
        if halt_reason:
            raise AgentRunHaltedError(halt_reason)

        verification, verify_in, verify_out, verify_cost = await verify_results(
            gateway=gateway,
            agent_def=agent_def,
            task_input=task_input,
            tool_actions=execution.tool_actions,
            model=model,
        )
        _accumulate(verify_in, verify_out, verify_cost)
        halt_reason = _check_limits()
        if halt_reason:
            raise AgentRunHaltedError(halt_reason)

        run.status = AgentRunStatus.COMPLETED if verification.passed else AgentRunStatus.FAILED
        run.outputs = {"output": verification.output, "reasoning": verification.reasoning}
        if not verification.passed:
            run.error = verification.reasoning

    except AgentRunHaltedError as halted:
        run.status = AgentRunStatus.HALTED
        run.halt_reason = halted.reason
    except (AgentRunLimitExceededError, ModelProviderError) as exc:
        run.status = AgentRunStatus.HALTED
        run.halt_reason = str(exc)
    except Exception as exc:
        # An agent run failing must never crash the worker/request that
        # started it -- the failure itself becomes the run's own record.
        run.status = AgentRunStatus.FAILED
        run.error = str(exc)

    run.completed_at = datetime.now(UTC)
    await db.flush()
    return run
