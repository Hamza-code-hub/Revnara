from app.agents.contracts import AgentDefinition, AgentLimits

# BE8.4: code-defined agent catalog (§2.8 Configuration Over Hardcoding),
# same pattern as app/organizations/permissions_catalog.py. Sprint 9's
# real Proposal Agent is the first production entry; `synthetic_test_agent`
# exists purely to exercise the runtime end to end (BE8's Definition of
# Done explicitly calls for "a synthetic end-to-end agent run") without
# waiting on a real domain agent to prove the infrastructure works.
AGENT_DEFINITIONS: dict[str, AgentDefinition] = {
    "synthetic_test_agent": AgentDefinition(
        id="synthetic_test_agent",
        version="1.0.0",
        owner="platform",
        purpose=(
            "Searches the company knowledge base and reports what it found -- exists to "
            "exercise the agent runtime end to end, not a real product feature."
        ),
        input_description=(
            "A natural-language question to research against the tenant's knowledge base."
        ),
        output_description="A short summary of the most relevant knowledge chunks found.",
        allowed_tools=["search_knowledge"],
        prohibited_tools=[],
        limits=AgentLimits(
            max_tool_calls=3, max_runtime_seconds=30, max_tokens=5_000, max_cost_usd=0.10
        ),
        validations=["output_is_non_empty", "output_cites_at_least_one_tool_result"],
        escalation_rules=["Halt and report if no relevant knowledge is found after 3 searches."],
    ),
}


class UnknownAgentError(Exception):
    pass


def get_agent_definition(agent_id: str) -> AgentDefinition:
    definition = AGENT_DEFINITIONS.get(agent_id)
    if definition is None:
        raise UnknownAgentError(f"Unknown agent: {agent_id!r}")
    return definition


def is_tool_allowed(agent_def: AgentDefinition, tool_name: str) -> bool:
    """BE8.4: the actual enforcement check -- allowed AND not prohibited.
    `prohibited_tools` always wins even if a tool is (mistakenly) present
    in both lists."""
    return tool_name in agent_def.allowed_tools and tool_name not in agent_def.prohibited_tools
