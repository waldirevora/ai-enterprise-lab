import asyncio

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.providers.deepseek import (
    DeepSeekProviderError,
)
from app.providers.ollama import (
    OllamaProviderError,
)
from app.schemas import GenerateRequest
from app.services import generation


def test_local_provider_internal_error_is_not_exposed(
    monkeypatch,
):
    internal_detail = (
        "SECRET_OLLAMA_INTERNAL_DETAIL"
    )

    async def fake_generate(
        *,
        model,
        prompt,
        temperature,
        num_ctx,
        max_output_tokens,
    ):
        raise OllamaProviderError(
            internal_detail
        )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                GenerateRequest(
                    provider="local_fast",
                    prompt="test",
                    max_output_tokens=64,
                )
            )
        )

    exc = exc_info.value

    assert exc.status_code == 503

    assert (
        exc.detail
        == "AI provider service unavailable."
    )

    assert (
        internal_detail
        not in exc.detail
    )


def test_external_provider_internal_error_is_not_exposed(
    monkeypatch,
):
    internal_detail = (
        "SECRET_DEEPSEEK_INTERNAL_DETAIL"
    )

    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    async def fake_generate(
        *,
        model,
        prompt,
        max_output_tokens,
    ):
        raise DeepSeekProviderError(
            internal_detail
        )

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_generate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                GenerateRequest(
                    provider="external_deep",
                    data_classification="public",
                    external_approved=True,
                    prompt="test",
                    max_output_tokens=64,
                )
            )
        )

    exc = exc_info.value

    assert exc.status_code == 503

    assert (
        exc.detail
        == "AI provider service unavailable."
    )

    assert (
        internal_detail
        not in exc.detail
    )
