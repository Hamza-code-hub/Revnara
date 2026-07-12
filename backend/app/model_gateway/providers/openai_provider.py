import httpx

from app.model_gateway.providers.base import ModelProvider, ProviderResponse


class OpenAIChatProvider(ModelProvider):
    """Calls OpenAI's real `/v1/chat/completions` API.

    Not exercised end-to-end anywhere in this codebase -- same situation
    as app/rag/embeddings.py's OpenAIEmbeddingProvider: no real
    model-provider API key configured in this environment
    (`Settings.model_provider_api_key` is empty). Mocked in tests rather
    than asserted against a real response body; revisit once a key
    exists (§4 Environment Prerequisites).
    """

    _BASE_URL = "https://api.openai.com/v1"

    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key

    async def complete(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ProviderResponse:
        async with httpx.AsyncClient(base_url=self._BASE_URL) as client:
            response = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens},
            )
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage", {})
            return ProviderResponse(
                content=data["choices"][0]["message"]["content"],
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
            )
