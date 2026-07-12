import pytest

from app.model_gateway.gateway import ModelCallResult, ModelGateway, ModelProviderError
from app.model_gateway.providers.base import ModelProvider, ProviderResponse


class _FakeProvider(ModelProvider):
    def __init__(self, *, response: ProviderResponse | None = None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.call_count = 0

    async def complete(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ProviderResponse:
        self.call_count += 1
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


@pytest.mark.asyncio
async def test_successful_call_records_model_prompt_version_tokens_cost_latency() -> None:
    primary = _FakeProvider(
        response=ProviderResponse(content="hello", input_tokens=1000, output_tokens=500)
    )
    gateway = ModelGateway(primary=primary)

    result = await gateway.complete(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        prompt_version="test-v1",
    )

    assert isinstance(result, ModelCallResult)
    assert result.content == "hello"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_version == "test-v1"
    assert result.input_tokens == 1000
    assert result.output_tokens == 500
    assert result.cost_usd > 0
    assert result.latency_ms >= 0
    assert result.provider_used == "primary"
    assert primary.call_count == 1


@pytest.mark.asyncio
async def test_primary_failure_falls_back_to_secondary_provider() -> None:
    primary = _FakeProvider(error=RuntimeError("primary down"))
    fallback = _FakeProvider(
        response=ProviderResponse(content="fallback response", input_tokens=10, output_tokens=5)
    )
    gateway = ModelGateway(primary=primary, fallback=fallback)

    result = await gateway.complete(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}], prompt_version="v1"
    )

    assert result.content == "fallback response"
    assert result.provider_used == "fallback"
    assert primary.call_count == 1
    assert fallback.call_count == 1


@pytest.mark.asyncio
async def test_both_providers_failing_raises_typed_error_not_raw_exception() -> None:
    primary = _FakeProvider(error=RuntimeError("primary down"))
    fallback = _FakeProvider(error=RuntimeError("fallback down"))
    gateway = ModelGateway(primary=primary, fallback=fallback)

    with pytest.raises(ModelProviderError):
        await gateway.complete(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}], prompt_version="v1"
        )


@pytest.mark.asyncio
async def test_primary_failure_without_fallback_raises_typed_error() -> None:
    primary = _FakeProvider(error=RuntimeError("primary down"))
    gateway = ModelGateway(primary=primary)

    with pytest.raises(ModelProviderError):
        await gateway.complete(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}], prompt_version="v1"
        )


@pytest.mark.asyncio
async def test_unknown_model_defaults_to_zero_cost_rather_than_crashing() -> None:
    primary = _FakeProvider(
        response=ProviderResponse(content="hi", input_tokens=100, output_tokens=50)
    )
    gateway = ModelGateway(primary=primary)

    result = await gateway.complete(
        model="some-unlisted-model",
        messages=[{"role": "user", "content": "hi"}],
        prompt_version="v1",
    )
    assert result.cost_usd == 0.0
