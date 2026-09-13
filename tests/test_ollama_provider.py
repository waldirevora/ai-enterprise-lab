import asyncio

import httpx
import pytest

from app.providers.ollama import (
    OllamaProvider,
    OllamaProviderError,
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


def create_provider() -> OllamaProvider:
    return OllamaProvider(
        "http://127.0.0.1:11434"
    )


def test_successful_request(
    monkeypatch,
):
    captured = {}

    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/generate",
    )

    response = httpx.Response(
        200,
        request=request,
        json={
            "response": "OK",
            "prompt_eval_count": 10,
            "eval_count": 5,
        },
    )

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
            captured=captured,
        ),
    )

    provider = create_provider()

    result = asyncio.run(
        provider.generate(
            model="qwen2.5-coder:3b",
            prompt="teste",
            temperature=0,
            num_ctx=4096,
            max_output_tokens=64,
        )
    )

    assert result["response"] == "OK"

    assert captured["url"] == (
        "http://127.0.0.1:11434/api/generate"
    )

    assert captured["json"]["model"] == (
        "qwen2.5-coder:3b"
    )

    assert captured["json"]["options"]["num_predict"] == 64


def test_model_not_found_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/generate",
    )

    response = httpx.Response(
        404,
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaProviderError,
        match="Ollama model not found",
    ):
        asyncio.run(
            provider.generate(
                model="modelo-inexistente",
                prompt="teste",
                temperature=0,
                num_ctx=4096,
                max_output_tokens=64,
            )
        )


def test_timeout_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/generate",
    )

    error = httpx.ReadTimeout(
        "timeout",
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            exception=error,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaProviderError,
        match="Ollama request timed out",
    ):
        asyncio.run(
            provider.generate(
                model="qwen2.5-coder:3b",
                prompt="teste",
                temperature=0,
                num_ctx=4096,
                max_output_tokens=64,
            )
        )


def test_connection_error_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/generate",
    )

    error = httpx.ConnectError(
        "connection failed",
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            exception=error,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        OllamaProviderError,
        match="Could not connect to Ollama",
    ):
        asyncio.run(
            provider.generate(
                model="qwen2.5-coder:3b",
                prompt="teste",
                temperature=0,
                num_ctx=4096,
                max_output_tokens=64,
            )
        )