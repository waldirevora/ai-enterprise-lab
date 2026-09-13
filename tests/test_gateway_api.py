from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import generation


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_provider_catalog_does_not_expose_api_key():
    response = client.get("/v1/providers")

    assert response.status_code == 200

    body = response.json()

    assert body["default"] == "local_fast"
    assert "local_fast" in body["providers"]
    assert "local_deep" in body["providers"]
    assert "external_deep" in body["providers"]

    serialized = response.text.lower()

    assert "api_key" not in serialized

    if settings.deepseek_api_key:
        assert settings.deepseek_api_key not in response.text


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
            "response": "LOCAL_TEST_OK",
            "prompt_eval_count": 10,
            "eval_count": 4,
            "total_duration": 250_000_000,
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
            "data_classification": "confidential",
            "prompt": "teste",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["provider"] == "local_fast"
    assert body["backend"] == "ollama"
    assert body["response"] == "LOCAL_TEST_OK"
    assert body["prompt_tokens"] == 10
    assert body["generated_tokens"] == 4
    assert body["total_duration_ms"] == 250.0


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

    assert response.json()["detail"] == (
        "Output token limit cannot exceed 2048."
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
            "data_classification": "confidential",
            "external_approved": True,
            "prompt": "teste",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "External providers are not allowed for "
        "'confidential' data."
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
                        "content": "DEEPSEEK_TEST_OK",
                        "reasoning_content": (
                            "internal reasoning must not leak"
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
            "data_classification": "public",
            "external_approved": True,
            "prompt": "teste publico",
            "max_output_tokens": 64,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["provider"] == "external_deep"
    assert body["backend"] == "deepseek"
    assert body["response"] == "DEEPSEEK_TEST_OK"
    assert body["reasoning_tokens"] == 6
    assert body["total_duration_ms"] == 500.0
    assert body["estimated_cost_usd"] is not None

    serialized = response.text

    assert "reasoning_content" not in serialized
    assert "internal reasoning must not leak" not in serialized