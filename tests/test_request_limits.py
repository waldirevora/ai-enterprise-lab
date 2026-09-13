import pytest

from app.core.config import settings
from app.policies.request_limits import validate_request_limits


def test_uses_default_output_limit():
    limits = validate_request_limits(
        prompt="teste",
        requested_max_output_tokens=None,
    )

    assert limits.max_output_tokens == settings.ai_max_output_tokens


def test_accepts_custom_output_limit():
    limits = validate_request_limits(
        prompt="teste",
        requested_max_output_tokens=512,
    )

    assert limits.max_output_tokens == 512


def test_rejects_output_limit_above_global_limit():
    with pytest.raises(
        ValueError,
        match="Output token limit cannot exceed",
    ):
        validate_request_limits(
            prompt="teste",
            requested_max_output_tokens=5000,
        )


def test_accepts_prompt_at_character_limit(monkeypatch):
    monkeypatch.setattr(
        settings,
        "ai_max_prompt_chars",
        10,
    )

    limits = validate_request_limits(
        prompt="1234567890",
        requested_max_output_tokens=100,
    )

    assert limits.max_output_tokens == 100


def test_rejects_prompt_above_character_limit(monkeypatch):
    monkeypatch.setattr(
        settings,
        "ai_max_prompt_chars",
        10,
    )

    with pytest.raises(
        ValueError,
        match="Prompt exceeds the limit",
    ):
        validate_request_limits(
            prompt="12345678901",
            requested_max_output_tokens=100,
        )