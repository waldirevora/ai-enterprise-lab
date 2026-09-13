import pytest

from app.core.config import settings
from app.policies.provider_policy import evaluate_provider_policy


@pytest.mark.parametrize(
    "provider,data_classification",
    [
        ("local_fast", "public"),
        ("local_fast", "internal"),
        ("local_fast", "confidential"),
        ("local_deep", "public"),
        ("local_deep", "internal"),
        ("local_deep", "confidential"),
    ],
)
def test_local_providers_are_allowed(
    provider,
    data_classification,
):
    decision = evaluate_provider_policy(
        provider=provider,
        data_classification=data_classification,
        external_approved=False,
    )

    assert decision.allowed is True


def test_external_provider_blocked_when_globally_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        False,
    )

    decision = evaluate_provider_policy(
        provider="external_deep",
        data_classification="public",
        external_approved=True,
    )

    assert decision.allowed is False
    assert decision.reason == "External AI is globally disabled."


@pytest.mark.parametrize(
    "data_classification",
    [
        "internal",
        "confidential",
    ],
)
def test_external_provider_blocks_non_public_data(
    monkeypatch,
    data_classification,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    decision = evaluate_provider_policy(
        provider="external_deep",
        data_classification=data_classification,
        external_approved=True,
    )

    assert decision.allowed is False


def test_external_provider_requires_explicit_approval(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    decision = evaluate_provider_policy(
        provider="external_deep",
        data_classification="public",
        external_approved=False,
    )

    assert decision.allowed is False


def test_external_provider_allows_public_data_with_approval(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    decision = evaluate_provider_policy(
        provider="external_deep",
        data_classification="public",
        external_approved=True,
    )

    assert decision.allowed is True