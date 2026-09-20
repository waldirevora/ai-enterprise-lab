import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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


def _request(
    provider: str = "local_fast",
) -> GenerateRequest:
    return GenerateRequest(
        prompt="GENERATION_OUTCOME_TEST",
        provider=provider,
        data_classification="public",
        external_approved=True,
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


def test_policy_rejection_records_rejected_preflight(
    monkeypatch,
):
    monkeypatch.setattr(
        generation,
        "evaluate_provider_policy",
        lambda **kwargs: SimpleNamespace(
            allowed=False,
            reason="Policy rejected.",
            reason_code="policy_rejected",
        ),
    )

    labels = {
        "provider": "local_fast",
        "backend": "preflight",
        "outcome": "rejected",
    }

    before = _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                _request()
            )
        )

    assert exc_info.value.status_code == 403

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    ) == before + 1


def test_request_limits_rejection_records_rejected_preflight(
    monkeypatch,
):
    monkeypatch.setattr(
        generation,
        "evaluate_provider_policy",
        _allow_policy,
    )

    def invalid_limits(
        **kwargs,
    ):
        raise ValueError(
            "Invalid request limits."
        )

    monkeypatch.setattr(
        generation,
        "validate_request_limits",
        invalid_limits,
    )

    labels = {
        "provider": "local_fast",
        "backend": "preflight",
        "outcome": "rejected",
    }

    before = _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                _request()
            )
        )

    assert exc_info.value.status_code == 422

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    ) == before + 1


def test_ollama_failure_records_unavailable(
    monkeypatch,
):
    class FakeOllamaError(Exception):
        pass

    async def fail_generate(
        **kwargs,
    ):
        raise FakeOllamaError(
            "internal ollama detail"
        )

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
        generation,
        "OllamaProviderError",
        FakeOllamaError,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fail_generate,
    )

    labels = {
        "provider": "local_fast",
        "backend": "ollama",
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                _request()
            )
        )

    assert exc_info.value.status_code == 503

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    ) == before + 1


def test_deepseek_failure_records_unavailable(
    monkeypatch,
):
    class FakeDeepSeekError(Exception):
        pass

    async def fail_generate(
        **kwargs,
    ):
        raise FakeDeepSeekError(
            "internal deepseek detail"
        )

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
        generation,
        "DeepSeekProviderError",
        FakeDeepSeekError,
    )

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fail_generate,
    )

    labels = {
        "provider": "external_deep",
        "backend": "deepseek",
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                _request(
                    provider="external_deep",
                )
            )
        )

    assert exc_info.value.status_code == 503

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    ) == before + 1


def test_unsupported_backend_records_unavailable(
    monkeypatch,
):
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
                    "backend": "future_backend",
                    "model": "test-model",
                },
            },
        },
    )

    labels = {
        "provider": "local_fast",
        "backend": "unsupported",
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                _request()
            )
        )

    assert exc_info.value.status_code == 501

    assert _metric_value(
        "ai_enterprise_generation_requests_total",
        labels,
    ) == before + 1
