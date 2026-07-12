from app.agents.contracts import AgentDefinition
from app.agents.planner import build_planner_system_prompt, parse_plan


def _agent_def(**overrides: object) -> AgentDefinition:
    defaults: dict[str, object] = {
        "id": "test_agent",
        "version": "1.0.0",
        "owner": "platform",
        "purpose": "test purpose",
        "input_description": "test",
        "output_description": "test",
        "allowed_tools": ["search_knowledge"],
        "prohibited_tools": [],
    }
    defaults.update(overrides)
    return AgentDefinition(**defaults)  # type: ignore[arg-type]


def test_parse_plan_reads_clean_json_array() -> None:
    raw = '[{"tool": "search_knowledge", "arguments": {"query": "flutter"}}]'
    plan = parse_plan(raw)
    assert len(plan) == 1
    assert plan[0].tool == "search_knowledge"
    assert plan[0].arguments == {"query": "flutter"}


def test_parse_plan_extracts_array_from_surrounding_prose() -> None:
    raw = (
        "Here is my plan:\n"
        '[{"tool": "search_knowledge", "arguments": {"query": "x"}}]\n'
        "Let me know if that works."
    )
    plan = parse_plan(raw)
    assert len(plan) == 1
    assert plan[0].tool == "search_knowledge"


def test_parse_plan_returns_empty_list_on_malformed_json() -> None:
    plan = parse_plan("this is not json at all")
    assert plan == []


def test_parse_plan_returns_empty_list_on_invalid_json_inside_brackets() -> None:
    plan = parse_plan("[not valid json]")
    assert plan == []


def test_parse_plan_skips_malformed_entries() -> None:
    raw = '[{"tool": "search_knowledge"}, "not a dict", {"no_tool_key": true}]'
    plan = parse_plan(raw)
    assert len(plan) == 1
    assert plan[0].tool == "search_knowledge"
    assert plan[0].arguments == {}


def test_planner_system_prompt_only_lists_allowed_tools() -> None:
    agent_def = _agent_def(allowed_tools=["search_knowledge"])
    prompt = build_planner_system_prompt(agent_def)
    assert "search_knowledge" in prompt
    assert "delete_everything" not in prompt


def test_planner_system_prompt_labels_context_as_untrusted_reference_data() -> None:
    """Blueprint §65 prompt-injection defense: the planner's own system
    prompt must explicitly instruct the model to treat retrieved content
    as inert data, never as instructions to follow."""
    prompt = build_planner_system_prompt(_agent_def())
    assert "not instructions" in prompt.lower() or "untrusted" in prompt.lower()
