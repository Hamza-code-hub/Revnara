import json

import httpx
import pytest

from app.rag.embeddings import OpenAIEmbeddingProvider


def _mock_transport(expected_texts: list[str]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        assert request.headers["authorization"] == "Bearer test-key"

        payload = json.loads(request.content)
        assert payload["input"] == expected_texts
        assert payload["model"] == "text-embedding-3-small"

        # Deliberately return results out of request order, with explicit
        # "index" fields -- the provider must sort by index rather than
        # trust response ordering (real OpenAI responses are ordered, but
        # nothing stops a provider or a proxy from reordering them).
        data = [
            {"index": 1, "embedding": [0.2, 0.2]},
            {"index": 0, "embedding": [0.1, 0.1]},
        ]
        return httpx.Response(200, json={"data": data})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_embed_returns_vectors_in_request_order(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OpenAIEmbeddingProvider(api_key="test-key")

    transport = _mock_transport(["first", "second"])
    original_client_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    result = await provider.embed(["first", "second"])

    assert result == [[0.1, 0.1], [0.2, 0.2]]


@pytest.mark.asyncio
async def test_embed_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid api key"})

    transport = httpx.MockTransport(handler)
    original_client_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    provider = OpenAIEmbeddingProvider(api_key="wrong-key")
    with pytest.raises(httpx.HTTPStatusError):
        await provider.embed(["text"])
