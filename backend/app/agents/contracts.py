from pydantic import BaseModel, Field


class AgentLimits(BaseModel):
    """BE8.3: the hard ceilings a run halts against (Blueprint §30) --
    enforced by the orchestrator (app/agents/runtime.py), not left to an
    agent's own judgement about when to stop."""

    max_tool_calls: int = 10
    max_runtime_seconds: int = 60
    max_tokens: int = 20_000
    max_cost_usd: float = 1.0


class AgentDefinition(BaseModel):
    """Blueprint §30's `AgentDefinition` schema -- config, not a hardcoded
    class per agent, so validating/listing agents is a data operation
    (app/agents/registry.py) rather than a code-review-only guarantee.

    `allowed_tools` is the actual allowlist the executor enforces;
    `prohibited_tools` is a defense-in-depth explicit denial list checked
    independently (a tool could theoretically be added to
    `allowed_tools` by mistake later -- `prohibited_tools` still wins).
    """

    id: str
    version: str
    owner: str
    purpose: str
    input_description: str
    output_description: str
    allowed_tools: list[str] = Field(default_factory=list)
    prohibited_tools: list[str] = Field(default_factory=list)
    limits: AgentLimits = Field(default_factory=AgentLimits)
    validations: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)
