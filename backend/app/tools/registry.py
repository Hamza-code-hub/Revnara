import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embeddings import EmbeddingProvider
from app.rag.retrieval import search


@dataclass(frozen=True)
class ToolContext:
    """Everything a tool handler might need, bundled once per invocation
    rather than each handler declaring its own bespoke parameter list --
    keeps `ToolHandler`'s signature uniform so the registry/executor
    don't need to know which dependencies a specific tool uses."""

    db: AsyncSession
    tenant_id: uuid.UUID
    actor_permissions: frozenset[str]
    embedder: EmbeddingProvider


ToolHandler = Callable[[ToolContext, dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler


async def _search_knowledge_handler(ctx: ToolContext, arguments: dict[str, Any]) -> Any:
    query = str(arguments.get("query", ""))
    limit = int(arguments.get("limit", 5))
    [query_embedding] = await ctx.embedder.embed([query])
    results = await search(
        ctx.db,
        query_embedding=query_embedding,
        tenant_id=ctx.tenant_id,
        actor_permissions=ctx.actor_permissions,
        limit=limit,
    )
    return [
        {"chunk_text": r.chunk_text, "source_type": r.source_type, "distance": r.distance}
        for r in results
    ]


# BE8.4's tool catalog -- code-defined, not hardcoded inline at each call
# site (§2.8), same pattern as app/organizations/permissions_catalog.py.
# `search_knowledge` is the one real tool available this sprint (reuses
# Sprint 5's retrieval.search) -- more tools land as later sprints'
# agents need them (e.g. Sprint 9's proposal-drafting tools), rather than
# speculatively registering tools nothing calls yet.
TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "search_knowledge": ToolDefinition(
        name="search_knowledge",
        description="Search the tenant's company knowledge base for relevant text chunks.",
        handler=_search_knowledge_handler,
    ),
}


class ToolNotAllowedError(Exception):
    """BE8.4: raised when a plan requests a tool outside the calling
    agent's `allowed_tools` (or explicitly in `prohibited_tools`) -- the
    first real enforcement of Blueprint §6.3's "no agent
    self-authorization" principle. Never silently skipped or logged-only;
    the executor always surfaces this as a blocked, audited tool call."""


class UnknownToolError(Exception):
    """Raised when a plan requests a tool that isn't in TOOL_REGISTRY at
    all -- distinct from [ToolNotAllowedError] (a real tool the agent
    isn't allowed to use) so callers can tell "doesn't exist" apart from
    "not permitted"."""


async def invoke_tool(
    *,
    tool_name: str,
    allowed_tools: list[str],
    prohibited_tools: list[str],
    context: ToolContext,
    arguments: dict[str, Any],
) -> Any:
    if tool_name not in allowed_tools or tool_name in prohibited_tools:
        raise ToolNotAllowedError(
            f"Tool {tool_name!r} is not in this agent's allowlist."
        )
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise UnknownToolError(f"Unknown tool: {tool_name!r}")
    return await tool.handler(context, arguments)
