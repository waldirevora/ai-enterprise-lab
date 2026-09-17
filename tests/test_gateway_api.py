import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import settings
from app.main import app
from app.rate_limit.models import (
    RateLimitDecision,
)
from app.services import generation


client = TestClient(app)


@pytest.fixture(autouse=True)
def allow_public_generate_rate_limit(
    monkeypatch,
):
    #
    # Os testes antigos do Gateway não
    # devem depender de um Redis real.
    #
    # Testes específicos abaixo substituem
    # este mock quando precisam verificar
    # 429 / 503 / chave de origem.
    #
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        return RateLimitDecision(
            allowed=True,
            remaining=999,
            retry_after_seconds=0,
        )

    monkeypatch.setattr(
        main_module,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )


def test_health_endpoint():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
    }


def test_provider_catalog_exposes_only_public_metadata():
    response = client.get(
        "/v1/providers"
    )

    assert response.status_code == 200

    body = response.json()

    assert body == {
        "default": "local_fast",
        "providers": {
            "local_fast": {
                "enabled": True,
            },
            "local_deep": {
                "enabled": True,
            },
            "external_deep": {
                "enabled": (
                    settings.external_ai_enabled
                ),
            },
        },
    }

    serialized = response.text.lower()

    assert "backend" not in serialized
    assert "model" not in serialized
    assert "ollama" not in serialized
    assert "deepseek" not in serialized
    assert "api_key" not in serialized

    if settings.deepseek_api_key:
        assert (
            settings.deepseek_api_key
            not in response.text
        )


def test_local_fast_generation(
    monkeypatch,
):
    async def fake_generate(
        *,
        model,
        prompt,
        temperature,
        num_ctx,
        max_output_tokens,
    ):
        return {
            "response": (
                "LOCAL_TEST_OK"
            ),
            "prompt_eval_count": 10,
            "eval_count": 4,
            "total_duration": (
                250_000_000
            ),
        }

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "local_fast",
            "data_classification": (
                "confidential"
            ),
            "prompt": "teste",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["provider"]
        == "local_fast"
    )

    assert (
        body["backend"]
        == "ollama"
    )

    assert (
        body["response"]
        == "LOCAL_TEST_OK"
    )

    assert (
        body["prompt_tokens"]
        == 10
    )

    assert (
        body["generated_tokens"]
        == 4
    )

    assert (
        body["total_duration_ms"]
        == 250.0
    )


def test_gateway_rejects_output_limit_above_maximum():
    response = client.post(
        "/v1/generate",
        json={
            "provider": "local_fast",
            "prompt": "teste",
            "max_output_tokens": 5000,
        },
    )

    assert response.status_code == 422

    assert (
        response.json()["detail"]
        == (
            "Output token limit "
            "cannot exceed 2048."
        )
    )


def test_external_confidential_data_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "external_deep",
            "data_classification": (
                "confidential"
            ),
            "external_approved": True,
            "prompt": "teste",
        },
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == (
            "External providers are not "
            "allowed for 'confidential' data."
        )
    )


def test_external_generation_does_not_expose_reasoning(
    monkeypatch,
):
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
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "DEEPSEEK_TEST_OK"
                        ),
                        "reasoning_content": (
                            "internal reasoning "
                            "must not leak"
                        ),
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 20,
                "completion_tokens_details": {
                    "reasoning_tokens": 6,
                },
            },
            "_gateway_duration_ms": 500.0,
        }

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "external_deep",
            "data_classification": (
                "public"
            ),
            "external_approved": True,
            "prompt": "teste publico",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["provider"]
        == "external_deep"
    )

    assert (
        body["backend"]
        == "deepseek"
    )

    assert (
        body["response"]
        == "DEEPSEEK_TEST_OK"
    )

    assert (
        body["reasoning_tokens"]
        == 6
    )

    assert (
        body["total_duration_ms"]
        == 500.0
    )

    assert (
        body["estimated_cost_usd"]
        is not None
    )

    serialized = response.text

    assert (
        "reasoning_content"
        not in serialized
    )

    assert (
        "internal reasoning must not leak"
        not in serialized
    )


def test_public_generate_forwards_rate_limit_policy(
    monkeypatch,
):
    captured = {}

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return RateLimitDecision(
            allowed=True,
            remaining=2,
            retry_after_seconds=0,
        )

    async def fake_generate(
        *,
        model,
        prompt,
        temperature,
        num_ctx,
        max_output_tokens,
    ):
        return {
            "response": "RATE_LIMIT_OK",
            "prompt_eval_count": 4,
            "eval_count": 2,
            "total_duration": (
                100_000_000
            ),
        }

    monkeypatch.setattr(
        main_module,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "local_fast",
            "prompt": "teste",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 200

    assert (
        captured["key"].startswith(
            "rate-limit:"
            "public-generate:"
        )
    )

    assert (
        captured["rate_per_minute"]
        == settings
        .rate_limit_public_generate_per_minute
    )

    assert (
        captured["burst"]
        == settings
        .rate_limit_public_generate_burst
    )


def test_public_generate_rate_limit_returns_429_before_generation(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Rate limit exceeded."
            ),
            headers={
                "Retry-After": "7",
            },
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "LLM generation must not run "
            "after rate limit denial."
        )

    monkeypatch.setattr(
        main_module,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        should_not_generate,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "local_fast",
            "prompt": "teste",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 429

    assert response.json() == {
        "detail": (
            "Rate limit exceeded."
        )
    }

    assert (
        response.headers[
            "Retry-After"
        ]
        == "7"
    )


def test_public_generate_rate_limit_unavailable_returns_503_before_generation(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Rate limit service "
                "unavailable."
            ),
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "LLM generation must not run "
            "when rate limit service "
            "is unavailable."
        )

    monkeypatch.setattr(
        main_module,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        should_not_generate,
    )

    response = client.post(
        "/v1/generate",
        json={
            "provider": "local_fast",
            "prompt": "teste",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service "
            "unavailable."
        )
    }


def test_public_generate_ignores_x_forwarded_for(
    monkeypatch,
):
    captured_keys = []

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        captured_keys.append(
            kwargs["key"]
        )

        return RateLimitDecision(
            allowed=True,
            remaining=2,
            retry_after_seconds=0,
        )

    async def fake_generate(
        *,
        model,
        prompt,
        temperature,
        num_ctx,
        max_output_tokens,
    ):
        return {
            "response": "ORIGIN_OK",
            "prompt_eval_count": 4,
            "eval_count": 2,
            "total_duration": (
                100_000_000
            ),
        }

    monkeypatch.setattr(
        main_module,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    first = client.post(
        "/v1/generate",
        headers={
            "X-Forwarded-For": (
                "198.51.100.10"
            ),
        },
        json={
            "provider": "local_fast",
            "prompt": "primeiro",
            "max_output_tokens": 64,
        },
    )

    second = client.post(
        "/v1/generate",
        headers={
            "X-Forwarded-For": (
                "203.0.113.99"
            ),
        },
        json={
            "provider": "local_fast",
            "prompt": "segundo",
            "max_output_tokens": 64,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert len(
        captured_keys
    ) == 2

    #
    # Se X-Forwarded-For fosse usado,
    # estes buckets seriam diferentes.
    #
    assert (
        captured_keys[0]
        == captured_keys[1]
    )