import logging
import time
from dataclasses import dataclass

from app.model_gateway.providers.base import ModelProvider

logger = logging.getLogger(__name__)

# BE8.1: USD per 1K tokens (input, output). Illustrative published OpenAI
# pricing, not fetched live -- revisit when real usage needs reconciling
# against an actual invoice. Config-not-hardcoded in spirit (one place,
# not scattered per call site), even though it's still a Python constant
# rather than a DB-backed table (no product need yet to change pricing
# without a deploy).
_PRICING_PER_1K_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
}
_DEFAULT_PRICING = (0.0, 0.0)


def _compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = _PRICING_PER_1K_TOKENS.get(model, _DEFAULT_PRICING)
    return round((input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price, 6)


@dataclass(frozen=True)
class ModelCallResult:
    content: str
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    provider_used: str


class ModelProviderError(Exception):
    """Raised when both the primary and (if configured) fallback provider
    fail -- callers see one typed error, never a raw provider exception
    leaking through (BE8's unit test requirement)."""


class ModelGateway:
    """BE8.1/BE8.9: the single entry point for every model call in this
    codebase -- records model/prompt-version/tokens/cost/latency per
    call (the foundation for Sprint 14's cost governance and Blueprint
    §71 observability), and automatically retries on a secondary
    provider if the primary errors (Blueprint §72 "Provider failover").

    Nothing outside `app/model_gateway/providers/` should import a model
    provider SDK/HTTP client directly -- enforced by a CI grep check
    (.github/workflows/backend-ci.yml), not just this docstring.
    """

    def __init__(
        self,
        *,
        primary: ModelProvider,
        fallback: ModelProvider | None = None,
        primary_name: str = "primary",
        fallback_name: str = "fallback",
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._primary_name = primary_name
        self._fallback_name = fallback_name

    async def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        prompt_version: str,
        max_tokens: int = 1000,
    ) -> ModelCallResult:
        start = time.monotonic()
        provider_used = self._primary_name
        try:
            response = await self._primary.complete(
                model=model, messages=messages, max_tokens=max_tokens
            )
        except Exception as primary_exc:
            if self._fallback is None:
                raise ModelProviderError(
                    f"Primary provider failed and no fallback is configured: {primary_exc}"
                ) from primary_exc
            logger.warning("model_gateway: primary provider failed, trying fallback", exc_info=True)
            provider_used = self._fallback_name
            try:
                response = await self._fallback.complete(
                    model=model, messages=messages, max_tokens=max_tokens
                )
            except Exception as fallback_exc:
                raise ModelProviderError(
                    f"Both primary and fallback providers failed. "
                    f"Primary: {primary_exc}. Fallback: {fallback_exc}."
                ) from fallback_exc

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = _compute_cost_usd(model, response.input_tokens, response.output_tokens)

        if provider_used == self._fallback_name:
            logger.warning(
                "model_gateway: call to %s completed via fallback provider (%s)",
                model,
                self._fallback_name,
            )

        return ModelCallResult(
            content=response.content,
            model=model,
            prompt_version=prompt_version,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            provider_used=provider_used,
        )
