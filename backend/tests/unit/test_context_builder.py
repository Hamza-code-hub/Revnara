import uuid

from app.rag.context_builder import (
    ConversationWindow,
    RunContextCache,
    assemble_chunks_within_budget,
    compute_step_budgets,
    rerank_by_task_relevance,
    summarize_to_fit,
)
from app.rag.retrieval import SearchResult


def _result(chunk_text: str, *, distance: float = 0.5) -> SearchResult:
    return SearchResult(
        chunk_id=uuid.uuid4(),
        source_type="portfolio_item",
        source_id=uuid.uuid4(),
        chunk_text=chunk_text,
        classification=None,
        distance=distance,
    )


def test_rerank_prefers_task_relevant_chunk_over_merely_similar_one() -> None:
    """BE8.6a: a chunk with lower vector distance (more similar to the
    original query) but no overlap with the actual task text should rank
    below a chunk with real task-relevant overlap, even at a higher
    distance -- otherwise re-ranking would just be a no-op."""
    irrelevant_but_close = _result("The weather today is sunny and warm.", distance=0.1)
    relevant_but_far = _result(
        "Our Flutter and FastAPI team delivered the inventory rebuild project.", distance=0.4
    )

    reranked = rerank_by_task_relevance(
        [irrelevant_but_close, relevant_but_far],
        task_text="Which team members have Flutter and FastAPI experience for this project?",
    )

    assert reranked[0] is relevant_but_far


def test_rerank_breaks_ties_by_distance() -> None:
    a = _result("Flutter FastAPI project alpha", distance=0.3)
    b = _result("Flutter FastAPI project beta", distance=0.1)

    reranked = rerank_by_task_relevance([a, b], task_text="Flutter FastAPI project")

    assert reranked[0] is b


def test_summarize_to_fit_returns_text_unchanged_when_within_budget() -> None:
    text = "Short text."
    assert summarize_to_fit(text, max_chars=1000) == text


def test_summarize_to_fit_truncates_at_sentence_boundary() -> None:
    text = "First sentence is here. Second sentence follows. Third one too."
    truncated = summarize_to_fit(text, max_chars=40)
    assert truncated == "First sentence is here."
    assert len(truncated) <= 40


def test_summarize_to_fit_hard_truncates_when_no_sentence_boundary_found() -> None:
    text = "a" * 500
    truncated = summarize_to_fit(text, max_chars=50)
    assert len(truncated) == 50


def test_assemble_chunks_within_budget_stops_at_the_limit_not_after() -> None:
    """BE8.6b: the highest-relevance chunks (already re-ranked) must be
    the ones kept -- lower-priority chunks are dropped once the budget
    is spent, not truncated to squeeze everything in."""
    results = [_result("A" * 50), _result("B" * 50), _result("C" * 50)]
    assembled = assemble_chunks_within_budget(results, max_chars=60)

    assert "A" * 50 in assembled
    assert "B" * 50 not in assembled
    assert "C" * 50 not in assembled


def test_compute_step_budgets_gives_independent_non_overlapping_ceilings() -> None:
    """BE8.6c: an oversized planner budget must not silently expand the
    executor's or verifier's own ceiling -- each is computed
    independently from the same model's context window."""
    budgets = compute_step_budgets(model="gpt-4o-mini")
    assert budgets.planner_chars > 0
    assert budgets.executor_chars > 0
    assert budgets.verifier_chars > 0
    # Executor gets the largest share (it does the deep work); planner
    # and verifier both get narrower views.
    assert budgets.executor_chars > budgets.planner_chars
    assert budgets.executor_chars > budgets.verifier_chars


def test_step_budgets_scale_with_the_models_context_window() -> None:
    small_model_budgets = compute_step_budgets(model="some-unlisted-8k-model")
    large_model_budgets = compute_step_budgets(model="gpt-4o-mini")
    assert large_model_budgets.executor_chars > small_model_budgets.executor_chars


def test_conversation_window_keeps_recent_turns_verbatim() -> None:
    window = ConversationWindow(max_turns=3)
    for i in range(3):
        window.add_turn(f"Turn {i}")
    rendered = window.render()
    assert "Turn 0" in rendered
    assert "Turn 2" in rendered
    assert window.summary == ""


def test_conversation_window_summarizes_older_turns_once_over_budget() -> None:
    """BE8.6e: a long conversation must not grow linearly forever --
    once history exceeds max_turns, the oldest turn is folded into a
    running summary rather than kept verbatim, while recent turns stay
    verbatim so a question about the recent context still works."""
    window = ConversationWindow(max_turns=2)
    window.add_turn("The client's budget is $50,000, discussed in turn zero.")
    window.add_turn("Turn one covers the timeline.")
    window.add_turn("Turn two covers the team.")

    rendered = window.render()
    assert "Turn one covers the timeline." in rendered
    assert "Turn two covers the team." in rendered
    # The oldest turn is no longer verbatim in recent_turns...
    assert "The client's budget is $50,000, discussed in turn zero." not in window.recent_turns
    # ...but its content is preserved (compressed) in the summary.
    assert "budget" in window.summary.lower()
    assert "[Earlier conversation summary]" in rendered


async def test_run_context_cache_only_fetches_once() -> None:
    cache = RunContextCache()
    call_count = 0

    async def _fetch() -> str:
        nonlocal call_count
        call_count += 1
        return "fetched value"

    first = await cache.get_or_fetch("company_profile", _fetch)
    second = await cache.get_or_fetch("company_profile", _fetch)

    assert first == "fetched value"
    assert second == "fetched value"
    assert call_count == 1
