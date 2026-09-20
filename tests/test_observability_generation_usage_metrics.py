import asyncio
from types import SimpleNamespace

from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
)
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


def _allow_policy(
    **kwargs,
):
    return SimpleNamespace(
        allowed=True,
        reason="Allowed.",
        reason_code="allowed",
    )


def _limits(
    **kwargs,
):
    return SimpleNamespace(
        max_output_tokens=64,
    )


def test_ollama_records_prompt_and_generated_tokens(
    monkeypatch,
):
    async def fake_generate(
        **kwargs,
    ):
        return {
            "response": "LOCAL_OK",
            "prompt_eval_count": 11,
            "eval_count": 5,
            "total_duration": 1_000_000,
        }

    monkeypatch.setattr(
        generation,
        "evaluate_provider_policy",
        _allow_policy,
    )

    monkeypatch.setattr(
        generation,
        "validate_request_limits",
        _limits,
    )

    monkeypatch.setattr(
        generation,
        "get_provider_catalog",
        lambda: {
            "providers": {
                "local_fast": {
                    "backend": "ollama",
                    "model": "test-model",
                },
            },
        },
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    prompt_labels = {
        "provider": "local_fast",
        "token_type": "prompt",
    }

    generated_labels = {
        "provider": "local_fast",
        "token_type": "generated",
    }

    prompt_before = _metric_value(
        "ai_enterprise_tokens_total",
        prompt_labels,
    )

    generated_before = _metric_value(
        "ai_enterprise_tokens_total",
        generated_labels,
    )

    response = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                prompt="LOCAL_USAGE_TEST",
                provider="local_fast",
                data_classification="public",
            )
        )
    )

    assert response.prompt_tokens == 11
    assert response.generated_tokens == 5

    assert _metric_value(
        "ai_enterprise_tokens_total",
        prompt_labels,
    ) == prompt_before + 11

    assert _metric_value(
        "ai_enterprise_tokens_total",
        generated_labels,
    ) == generated_before + 5


def test_deepseek_records_usage_breakdowns_and_cost(
    monkeypatch,
):
    async def fake_generate(
        **kwargs,
    ):
        return {
            "choices": [
                {
                    "message": {
                        "content": "DEEP_OK",
                    },
                },
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
            "_gateway_duration_ms": 20.0,
        }

    monkeypatch.setattr(
        generation,
        "evaluate_provider_policy",
        _allow_policy,
    )

    monkeypatch.setattr(
        generation,
        "validate_request_limits",
        _limits,
    )

    monkeypatch.setattr(
        generation,
        "get_provider_catalog",
        lambda: {
            "providers": {
                "external_deep": {
                    "backend": "deepseek",
                    "model": "test-model",
                },
            },
        },
    )

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_generate,
    )

    monkeypatch.setattr(
        generation,
        "estimate_deepseek_cost",
        lambda **kwargs: SimpleNamespace(
            pricing_tier="off_peak",
            estimated_cost_usd=0.00125,
        ),
    )

    token_expectations = {
        "prompt": 10,
        "generated": 4,
        "reasoning": 1,
        "cache_hit": 2,
        "cache_miss": 8,
    }

    before = {
        token_type: _metric_value(
            "ai_enterprise_tokens_total",
            {
                "provider": "external_deep",
                "token_type": token_type,
            },
        )
        for token_type in token_expectations
    }

    cost_labels = {
        "provider": "external_deep",
        "pricing_tier": "off_peak",
    }

    cost_before = _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        cost_labels,
    )

    response = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                prompt="DEEP_USAGE_TEST",
                provider="external_deep",
                data_classification="public",
                external_approved=True,
            )
        )
    )

    assert response.pricing_tier == "off_peak"
    assert response.estimated_cost_usd == 0.00125

    for token_type, expected_delta in (
        token_expectations.items()
    ):
        assert _metric_value(
            "ai_enterprise_tokens_total",
            {
                "provider": "external_deep",
                "token_type": token_type,
            },
        ) == before[token_type] + expected_delta

    assert _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        cost_labels,
    ) == cost_before + 0.00125


def test_invalid_pricing_tier_is_not_recorded():
    labels = {
        "provider": "external_deep",
        "pricing_tier": "unexpected",
    }

    before = _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        labels,
    )

    generation._record_generation_usage(
        response=GenerateResponse(
            provider="external_deep",
            backend="deepseek",
            model="test-model",
            response="OK",
            pricing_tier="unexpected",
            estimated_cost_usd=10.0,
        )
    )

    assert _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        labels,
    ) == before

def test_none_and_zero_token_usage_is_not_recorded():
    token_types = (
        "prompt",
        "generated",
        "reasoning",
        "cache_hit",
        "cache_miss",
    )

    before = {
        token_type: _metric_value(
            "ai_enterprise_tokens_total",
            {
                "provider": "external_deep",
                "token_type": token_type,
            },
        )
        for token_type in token_types
    }

    cost_labels = {
        "provider": "external_deep",
        "pricing_tier": "off_peak",
    }

    cost_before = _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        cost_labels,
    )

    generation._record_generation_usage(
        response=GenerateResponse(
            provider="external_deep",
            backend="deepseek",
            model="test-model",
            response="OK",
            prompt_tokens=None,
            generated_tokens=0,
            reasoning_tokens=None,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=None,
            pricing_tier="off_peak",
            estimated_cost_usd=None,
        )
    )

    for token_type in token_types:
        assert _metric_value(
            "ai_enterprise_tokens_total",
            {
                "provider": "external_deep",
                "token_type": token_type,
            },
        ) == before[token_type]

    assert _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        cost_labels,
    ) == cost_before


def test_zero_external_cost_is_not_recorded():
    labels = {
        "provider": "external_deep",
        "pricing_tier": "off_peak",
    }

    before = _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        labels,
    )

    generation._record_generation_usage(
        response=GenerateResponse(
            provider="external_deep",
            backend="deepseek",
            model="test-model",
            response="OK",
            pricing_tier="off_peak",
            estimated_cost_usd=0.0,
        )
    )

    assert _metric_value(
        "ai_enterprise_estimated_external_cost_usd_total",
        labels,
    ) == before
