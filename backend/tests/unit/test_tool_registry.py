import pytest

from app.tools.registry import ToolNotAllowedError, UnknownToolError, invoke_tool


class _FakeContext:
    pass


@pytest.mark.asyncio
async def test_invoke_tool_not_in_allowed_list_raises_typed_error() -> None:
    with pytest.raises(ToolNotAllowedError):
        await invoke_tool(
            tool_name="search_knowledge",
            allowed_tools=[],
            prohibited_tools=[],
            context=_FakeContext(),  # type: ignore[arg-type]
            arguments={},
        )


@pytest.mark.asyncio
async def test_invoke_tool_explicitly_prohibited_raises_typed_error_even_if_allowed() -> None:
    with pytest.raises(ToolNotAllowedError):
        await invoke_tool(
            tool_name="search_knowledge",
            allowed_tools=["search_knowledge"],
            prohibited_tools=["search_knowledge"],
            context=_FakeContext(),  # type: ignore[arg-type]
            arguments={},
        )


@pytest.mark.asyncio
async def test_invoke_unknown_tool_raises_typed_error() -> None:
    with pytest.raises(UnknownToolError):
        await invoke_tool(
            tool_name="does_not_exist",
            allowed_tools=["does_not_exist"],
            prohibited_tools=[],
            context=_FakeContext(),  # type: ignore[arg-type]
            arguments={},
        )
