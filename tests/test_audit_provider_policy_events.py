import asyncio

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.schemas import GenerateRequest
from app.services import generation


def capture_events(
    monkeypatch,
):
    events = []

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        generation,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    return events


def test_external_provider_allowed_emits_safe_event(
    monkeypatch,
):
    events = capture_events(
        monkeypatch
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
        return {
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
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 10,
            },
            "_gateway_duration_ms": 10.0,
        }

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_generate,
    )

    result = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                provider="external_deep",
                data_classification="public",
                external_approved=True,
                prompt="SECRET_PROMPT",
                max_output_tokens=64,
            )
        )
    )

    assert result.response == "OK"

    assert events == [
        {
            "event_type": (
                "provider.external.allowed"
            ),
            "outcome": "allowed",
            "provider": "external_deep",
            "classification": "public",
            "reason_code": (
                "external_provider_authorized"
            ),
        }
    ]

    assert (
        "SECRET_PROMPT"
        not in repr(
            events
        )
    )


def test_external_provider_global_disable_is_audited(
    monkeypatch,
):
    events = capture_events(
        monkeypatch
    )

    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        False,
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
                    prompt="SECRET_PROMPT",
                )
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        exc_info.value.detail
        == "External AI is globally disabled."
    )

    assert events == [
        {
            "event_type": (
                "provider.external.blocked"
            ),
            "outcome": "denied",
            "provider": "external_deep",
            "classification": "public",
            "reason_code": (
                "external_ai_globally_disabled"
            ),
            "metadata": {
                "status_code": 403,
            },
        }
    ]

    assert (
        "SECRET_PROMPT"
        not in repr(
            events
        )
    )


def test_external_provider_non_public_data_is_audited(
    monkeypatch,
):
    events = capture_events(
        monkeypatch
    )

    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                GenerateRequest(
                    provider="external_deep",
                    data_classification=(
                        "confidential"
                    ),
                    external_approved=True,
                    prompt="SECRET_PROMPT",
                )
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert events == [
        {
            "event_type": (
                "provider.external.blocked"
            ),
            "outcome": "denied",
            "provider": "external_deep",
            "classification": (
                "confidential"
            ),
            "reason_code": (
                "external_provider_non_public_data"
            ),
            "metadata": {
                "status_code": 403,
            },
        }
    ]

    assert (
        "SECRET_PROMPT"
        not in repr(
            events
        )
    )


def test_external_provider_missing_approval_is_audited(
    monkeypatch,
):
    events = capture_events(
        monkeypatch
    )

    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generation.generate_text(
                GenerateRequest(
                    provider="external_deep",
                    data_classification="public",
                    external_approved=False,
                    prompt="SECRET_PROMPT",
                )
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert events == [
        {
            "event_type": (
                "provider.external.blocked"
            ),
            "outcome": "denied",
            "provider": "external_deep",
            "classification": "public",
            "reason_code": (
                "external_provider_approval_required"
            ),
            "metadata": {
                "status_code": 403,
            },
        }
    ]

    assert (
        "SECRET_PROMPT"
        not in repr(
            events
        )
    )


def test_local_provider_does_not_emit_external_event(
    monkeypatch,
):
    events = capture_events(
        monkeypatch
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
            "response": "LOCAL_OK",
            "prompt_eval_count": 10,
            "eval_count": 5,
            "total_duration": 1_000_000,
        }

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_generate,
    )

    result = asyncio.run(
        generation.generate_text(
            GenerateRequest(
                provider="local_fast",
                data_classification="internal",
                prompt="SECRET_PROMPT",
                max_output_tokens=64,
            )
        )
    )

    assert result.response == "LOCAL_OK"
    assert events == []
