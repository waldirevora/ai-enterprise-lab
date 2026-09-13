import asyncio

import httpx
import pytest

from app.providers.deepseek import (
    DeepSeekProvider,
    DeepSeekProviderError,
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
        headers,
        json,
    ):
        if self.captured is not None:
            self.captured["url"] = url
            self.captured["headers"] = headers
            self.captured["json"] = json

        if self.exception is not None:
            raise self.exception

        return self.response


def create_provider(
    api_key: str = "test-key",
) -> DeepSeekProvider:
    return DeepSeekProvider(
        base_url="https://api.deepseek.com",
        api_key=api_key,
        thinking_enabled=True,
        reasoning_effort="high",
    )


def test_rejects_missing_api_key():
    provider = create_provider(
        api_key="",
    )

    with pytest.raises(
        DeepSeekProviderError,
        match="API key is not configured",
    ):
        asyncio.run(
            provider.generate(
                model="deepseek-v4-pro",
                prompt="teste",
                max_output_tokens=64,
            )
        )


def test_successful_request(
    monkeypatch,
):
    captured = {}

    request = httpx.Request(
        "POST",
        "https://api.deepseek.com/chat/completions",
    )

    response = httpx.Response(
        200,
        request=request,
        json={
            "choices": [
                {
                    "message": {
                        "content": "OK",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
            },
        },
    )

    monkeypatch.setattr(
        "app.providers.deepseek.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
            captured=captured,
        ),
    )

    provider = create_provider()

    result = asyncio.run(
        provider.generate(
            model="deepseek-v4-pro",
            prompt="teste",
            max_output_tokens=64,
        )
    )

    assert result["choices"][0]["message"]["content"] == "OK"
    assert "_gateway_duration_ms" in result

    assert captured["url"] == (
        "https://api.deepseek.com/chat/completions"
    )

    assert captured["headers"]["Authorization"] == (
        "Bearer test-key"
    )

    assert captured["json"]["model"] == "deepseek-v4-pro"
    assert captured["json"]["max_tokens"] == 64

    assert captured["json"]["thinking"] == {
        "type": "enabled"
    }

    assert captured["json"]["reasoning_effort"] == "high"


def test_authentication_error_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "https://api.deepseek.com/chat/completions",
    )

    response = httpx.Response(
        401,
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.deepseek.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            response=response,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        DeepSeekProviderError,
        match="DeepSeek authentication failed",
    ):
        asyncio.run(
            provider.generate(
                model="deepseek-v4-pro",
                prompt="teste",
                max_output_tokens=64,
            )
        )


def test_timeout_error_is_sanitized(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "https://api.deepseek.com/chat/completions",
    )

    timeout_error = httpx.ReadTimeout(
        "timeout",
        request=request,
    )

    monkeypatch.setattr(
        "app.providers.deepseek.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(
            exception=timeout_error,
        ),
    )

    provider = create_provider()

    with pytest.raises(
        DeepSeekProviderError,
        match="DeepSeek request timed out",
    ):
        asyncio.run(
            provider.generate(
                model="deepseek-v4-pro",
                prompt="teste",
                max_output_tokens=64,
            )
        )