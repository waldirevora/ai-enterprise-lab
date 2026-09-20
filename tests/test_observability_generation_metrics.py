import asyncio

from app.core.config import settings
from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.schemas import GenerateRequest
from app.services import generation


def _metric_value(
    name: str,
    labels: dict[str, str],
) -> float:
    value = METRICS_REGISTRY.get_sample_value(
        name,
        labels,
    )

    return float(
        value or 0.0
    )


def test_local_generation_records_success_metrics(
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
            "response": "LOCAL_OK",
            "prompt_eval_count": 10,
            "eval_count": 4,
            "total_duration": 250_000_000,
        }

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    request_labels = {
        "provider": "local_fast",
        "backend": "ollama",
        "outcome": "success",
    }

    duration_labels = {
        "provider": "local_fast",
        "backend": "ollama",
    }

    requests_before = _metric_value(
        "ai_enterprise_generation_requests_total",
        request_labels,
    )

    duration_count_before = _metric_value(
        "ai_enterprise_generation_duration_seconds_count",
        duration_labels,
    )

    response = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                provider="local_fast",
                prompt="LOCAL_METRICS_TEST",
                max_output_tokens=64,
            )
        )
    )

    assert response.response == "LOCAL_OK"

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        request_labels,
    ) == requests_before + 1

    assert _metric_value(
        "ai_enterprise_generation_duration_seconds_count",
        duration_labels,
    ) == duration_count_before + 1


def test_deepseek_generation_records_success_metrics(
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
                        "content": "DEEPSEEK_OK",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 4,
                "prompt_cache_hit_tokens": 2,
                "prompt_cache_miss_tokens": 8,
                "completion_tokens_details": {
                    "reasoning_tokens": 1,
                },
            },
            "_gateway_duration_ms": 50.0,
        }

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_generate,
    )

    request_labels = {
        "provider": "external_deep",
        "backend": "deepseek",
        "outcome": "success",
    }

    duration_labels = {
        "provider": "external_deep",
        "backend": "deepseek",
    }

    requests_before = _metric_value(
        "ai_enterprise_generation_requests_total",
        request_labels,
    )

    duration_count_before = _metric_value(
        "ai_enterprise_generation_duration_seconds_count",
        duration_labels,
    )

    response = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                provider="external_deep",
                data_classification="public",
                external_approved=True,
                prompt="PUBLIC_METRICS_TEST",
                max_output_tokens=64,
            )
        )
    )

    assert response.response == "DEEPSEEK_OK"

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        request_labels,
    ) == requests_before + 1

    assert _metric_value(
        "ai_enterprise_generation_duration_seconds_count",
        duration_labels,
    ) == duration_count_before + 1
