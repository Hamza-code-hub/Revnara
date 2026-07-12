import pytest

from app.agents.contracts import AgentDefinition
from app.agents.registry import UnknownAgentError, get_agent_definition, is_tool_allowed


def test_get_known_agent_definition() -> None:
    definition = get_agent_definition("synthetic_test_agent")
    assert definition.id == "synthetic_test_agent"
    assert "search_knowledge" in definition.allowed_tools


def test_unknown_agent_raises_typed_error() -> None:
    with pytest.raises(UnknownAgentError):
        get_agent_definition("does_not_exist")


def test_tool_in_allowlist_is_allowed() -> None:
    agent_def = AgentDefinition(
        id="test",
        version="1.0.0",
        owner="platform",
        purpose="test",
        input_description="test",
        output_description="test",
        allowed_tools=["search_knowledge"],
        prohibited_tools=[],
    )
    assert is_tool_allowed(agent_def, "search_knowledge") is True


def test_tool_not_in_allowlist_is_blocked() -> None:
    agent_def = AgentDefinition(
        id="test",
        version="1.0.0",
        owner="platform",
        purpose="test",
        input_description="test",
        output_description="test",
        allowed_tools=["search_knowledge"],
        prohibited_tools=[],
    )
    assert is_tool_allowed(agent_def, "delete_everything") is False


def test_prohibited_tool_is_blocked_even_if_also_in_allowed_list() -> None:
    """Defense in depth: prohibited_tools always wins, even against a
    mistake where the same tool ended up in both lists."""
    agent_def = AgentDefinition(
        id="test",
        version="1.0.0",
        owner="platform",
        purpose="test",
        input_description="test",
        output_description="test",
        allowed_tools=["search_knowledge"],
        prohibited_tools=["search_knowledge"],
    )
    assert is_tool_allowed(agent_def, "search_knowledge") is False
