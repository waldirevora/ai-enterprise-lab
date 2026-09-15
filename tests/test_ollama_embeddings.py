import asyncio

import httpx
import pytest

from app.providers.ollama_embeddings import (
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderError,
)


class FakeAsyncClient:
    def __init__(
        self,
        *,
        response=None,
        exception=None,
        captured=None,
    ):
        self.response = response
        self.exception = exception
        self.captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def post(
        self,
        url,
        *,
        json,
    ):
        if self.captured is not None:
            self.captured["url"] = url
            self.captured["json"] = json

        if self.exception is not None:
            raise self.exception

        return self.response


def create_provider(
    dimensions: int = 1024,
) -> OllamaEmbeddingProvider:
    return OllamaEmbeddingProvider(
        base_url="http://127.0.0.1:11434",
        expected_dimensions=dimensions,
    )


def test_successful_embedding(
    monkeypatch,
):
    captured = {}

    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/embed",
    )

    response = httpx.Response(
        200,
        request=request,
        json={
            "embeddings": [
                [0.1] * 1024
            ]
        },
    )

    monkeypatch.setattr(
        "app.providers.ollama_embeddings.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
            captured=captured,
        ),
    )

    provider = create_provider()

    result = asyncio.run(
        provider.embed(
            model="qwen3-embedding:0.6b",
            text="teste",
        )
    )

    assert len(result) == 1024

    assert captured["url"] == (
        "http://127.0.0.1:11434/api/embed"
    )

    assert captured["json"]["model"] == (
        "qwen3-embedding:0.6b"
    )

    assert captured["json"]["input"] == "teste"


def test_rejects_wrong_dimensions(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/embed",
    )

    response = httpx.Response(
        200,
        request=request,
        json={
            "embeddings": [
                [0.1] * 768
            ]
        },
    )

    monkeypatch.setattr(
        "app.providers.ollama_embeddings.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaEmbeddingProviderError,
        match="Unexpected embedding dimensions",
    ):
        asyncio.run(
            provider.embed(
                model="qwen3-embedding:0.6b",
                text="teste",
            )
        )


def test_timeout_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/embed",
    )

    error = httpx.ReadTimeout(
        "timeout",
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.ollama_embeddings.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            exception=error,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaEmbeddingProviderError,
        match="embedding request timed out",
    ):
        asyncio.run(
            provider.embed(
                model="qwen3-embedding:0.6b",
                text="teste",
            )
        )


def test_connection_error_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/embed",
    )

    error = httpx.ConnectError(
        "connection failed",
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.ollama_embeddings.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            exception=error,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaEmbeddingProviderError,
        match="Could not connect",
    ):
        asyncio.run(
            provider.embed(
                model="qwen3-embedding:0.6b",
                text="teste",
            )
        )