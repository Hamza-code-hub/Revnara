from abc import ABC, abstractmethod

import httpx


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Calls OpenAI's real `/v1/embeddings` API (`text-embedding-3-small`,
    `app.rag.models.EMBEDDING_DIMENSIONS`-dimensional).

    Not exercised end-to-end anywhere in this codebase -- like Sprint 2's
    Supabase Auth integration before a real project existed, there is no
    real model-provider API key configured in this environment
    (`Settings.model_provider_api_key` is empty). Mocked in tests rather
    than asserted against a real response body; revisit once a key exists
    (§4 Environment Prerequisites, and Sprint 8's model gateway may
    supersede calling this directly).
    """

    _MODEL = "text-embedding-3-small"
    _BASE_URL = "https://api.openai.com/v1"

    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(base_url=self._BASE_URL) as client:
            response = await client.post(
                "/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._MODEL, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            # Sort explicitly by the "index" each result carries rather
            # than trusting response ordering to match request ordering.
            ordered = sorted(data["data"], key=lambda item: item["index"])
            return [item["embedding"] for item in ordered]
