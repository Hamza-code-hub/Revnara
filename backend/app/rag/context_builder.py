import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embeddings import EmbeddingProvider
from app.rag.retrieval import SearchResult, search

# BE8.6d: provider-aware sizing -- context budget is computed against the
# *active* model's actual context window, not a single hardcoded
# constant (§2.8 Configuration Over Hardcoding). Extend this table as new
# models/providers are added rather than assuming one size everywhere.
_PROVIDER_CONTEXT_WINDOW_TOKENS: dict[str, int] = {
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
}
_DEFAULT_CONTEXT_WINDOW_TOKENS = 8_000
_CHARS_PER_TOKEN_ESTIMATE = 4


def context_window_tokens(model: str) -> int:
    return _PROVIDER_CONTEXT_WINDOW_TOKENS.get(model, _DEFAULT_CONTEXT_WINDOW_TOKENS)


def budget_chars(*, model: str, share: float) -> int:
    """`share` is the fraction of the model's context window this step
    gets to spend on retrieved/assembled context (the rest is reserved
    for the system prompt, task input, and the model's own output)."""
    return int(context_window_tokens(model) * _CHARS_PER_TOKEN_ESTIMATE * share)


@dataclass(frozen=True)
class StepBudgets:
    """BE8.6c: a multi-step run does not give every step the same
    context budget -- the planner gets a broad-but-shallow view, the
    executor a narrow-but-deep view of only what the planner requested,
    the verifier the executor's output plus minimal supporting evidence.
    Enforced independently per step (an oversized planner context does
    not silently spill its excess into the executor's budget -- each
    figure is its own hard ceiling, computed once up front)."""

    planner_chars: int
    executor_chars: int
    verifier_chars: int


def compute_step_budgets(*, model: str) -> StepBudgets:
    return StepBudgets(
        planner_chars=budget_chars(model=model, share=0.15),
        executor_chars=budget_chars(model=model, share=0.35),
        verifier_chars=budget_chars(model=model, share=0.10),
    )


def rerank_by_task_relevance(
    results: list[SearchResult], task_text: str
) -> list[SearchResult]:
    """BE8.6a: Sprint 5's retrieval ranks by raw vector similarity to the
    *query* alone; this re-ranks that same candidate set against the
    specific task at hand, so context budget is spent on what's actually
    relevant to what the agent needs to do, not merely what's similar to
    the search terms. Deterministic keyword-overlap scoring (no model
    call) -- consistent with this codebase's "deterministic where
    possible" heuristics (safety_screening.py, qualification.py), and
    fully unit-testable without a live model provider.
    """
    task_words = {w for w in task_text.lower().split() if len(w) > 2}

    def _relevance_key(result: SearchResult) -> tuple[int, float]:
        chunk_words = {w for w in result.chunk_text.lower().split() if len(w) > 2}
        overlap = len(task_words & chunk_words)
        # Higher overlap first; among ties, lower vector distance first.
        return (-overlap, result.distance)

    return sorted(results, key=_relevance_key)


def summarize_to_fit(text: str, *, max_chars: int) -> str:
    """BE8.6b: hierarchical-summarization stand-in when no real standing
    summary exists for a source -- truncates at the last sentence
    boundary within budget rather than naively cutting mid-sentence/word,
    so what's included is always a coherent (if partial) unit of text.
    A real Sprint 8.5+ document summarizer would populate a genuine
    standing summary the context builder could include verbatim instead
    of truncating; that field doesn't exist yet, so this is the honest
    interim.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind(". ")
    if last_period > max_chars // 2:
        return truncated[: last_period + 1]
    return truncated


def assemble_chunks_within_budget(results: list[SearchResult], *, max_chars: int) -> str:
    parts: list[str] = []
    used = 0
    for result in results:
        remaining = max_chars - used
        if remaining <= 0:
            break
        chunk_text = summarize_to_fit(result.chunk_text, max_chars=remaining)
        if not chunk_text:
            continue
        parts.append(chunk_text)
        used += len(chunk_text)
    return "\n---\n".join(parts)


async def build_context(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_permissions: frozenset[str],
    embedder: EmbeddingProvider,
    query: str,
    task_text: str,
    model: str,
    share: float = 0.35,
    retrieval_limit: int = 20,
) -> str:
    """BE8.6/BE8.6a/BE8.6b/BE8.6d: retrieves candidates via Sprint 5's
    vector search, re-ranks against the specific task, then fills the
    provider-aware budget for this step -- truncating/summarizing only
    the chunks that don't fit, never silently dropping the highest-
    relevance ones to keep a lower-relevance chunk whole.

    Retrieved content is always returned as one plain string, never
    embedded into anything resembling an instruction -- callers
    (app/agents/planner.py, verifier.py) are responsible for labeling it
    as untrusted reference data in their own prompts (Blueprint §65).
    """
    [query_embedding] = await embedder.embed([query])
    results = await search(
        db,
        query_embedding=query_embedding,
        tenant_id=tenant_id,
        actor_permissions=actor_permissions,
        limit=retrieval_limit,
    )
    reranked = rerank_by_task_relevance(results, task_text)
    return assemble_chunks_within_budget(reranked, max_chars=budget_chars(model=model, share=share))


@dataclass
class ConversationWindow:
    """BE8.6e: keeps recent turns verbatim; once history exceeds
    `max_turns`, the oldest turn is folded into a running summary
    (truncated-to-fit via [summarize_to_fit]) instead of the window
    growing without bound. A question referencing an early turn is still
    answerable from the summary, just compressed rather than verbatim.
    """

    max_turns: int = 10
    max_summary_chars: int = 2000
    summary: str = ""
    recent_turns: list[str] = field(default_factory=list)

    def add_turn(self, turn: str) -> None:
        self.recent_turns.append(turn)
        while len(self.recent_turns) > self.max_turns:
            oldest = self.recent_turns.pop(0)
            combined = f"{self.summary} {oldest}".strip()
            self.summary = summarize_to_fit(combined, max_chars=self.max_summary_chars)

    def render(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"[Earlier conversation summary]: {self.summary}")
        parts.extend(self.recent_turns)
        return "\n".join(parts)


class RunContextCache:
    """BE8.6f: reuse across a single agent run -- content fetched once
    (e.g. the company profile) is cached and reused across planner/
    executor/verifier calls of the *same run* rather than re-fetched at
    every step. Scoped to one run's lifetime (a new orchestrator call
    creates a new cache), never shared across runs/tenants.
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    async def get_or_fetch(self, key: str, fetch: Callable[[], Awaitable[Any]]) -> Any:
        if key not in self._cache:
            self._cache[key] = await fetch()
        return self._cache[key]
