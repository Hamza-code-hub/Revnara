from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation the planner requests (Blueprint §30/§31).
    Structurally identical whether it came from a real model response or
    a test fixture -- the executor treats both the same way."""

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
