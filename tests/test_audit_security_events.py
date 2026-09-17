import asyncio

import pytest
from fastapi import HTTPException

from app.access import dependencies
from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
)
from app.access.context import PrincipalContext
from app.rate_limit import http as rate_limit_http
from app.rate_limit.limiter import (
    RateLimitUnavailableError,
)
from app.rate_limit.models import (
    RateLimitDecision,
)


def make_context() -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=20,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification="internal",
    )


def test_auth_success_emits_safe_event(
    monkeypatch,
):
    events = []

    async def fake_authenticate(
        token,
    ):
        assert (
            token
            == "super-secret-token"
        )

        return make_context()

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    monkeypatch.setattr(
        dependencies,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    context = asyncio.run(
        dependencies.require_principal_context(
            authorization=(
                "Bearer super-secret-token"
            )
        )
    )

    assert context.principal_id == 10

    assert events == [
        {
            "event_type": "auth.success",
            "outcome": "success",
            "organization_id": 20,
            "principal_id": 10,
            "reason_code": (
                "credential_valid"
            ),
            "metadata": {
                "status_code": 200,
            },
        }
    ]

    assert (
        "super-secret-token"
        not in repr(
            events
        )
    )


def test_missing_credential_emits_failure(
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
        dependencies,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies
            .require_principal_context(
                authorization=None
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert events == [
        {
            "event_type": "auth.failure",
            "outcome": "failure",
            "reason_code": (
                "credential_missing_or_malformed"
            ),
            "metadata": {
                "status_code": 401,
            },
        }
    ]


def test_invalid_credential_emits_failure(
    monkeypatch,
):
    events = []

    async def fake_authenticate(
        token,
    ):
        raise AuthenticationError(
            "internal credential detail"
        )

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    monkeypatch.setattr(
        dependencies,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies
            .require_principal_context(
                authorization=(
                    "Bearer invalid-secret"
                )
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert events[0][
        "event_type"
    ] == "auth.failure"

    assert events[0][
        "reason_code"
    ] == "credential_invalid"

    serialized = repr(
        events
    )

    assert (
        "invalid-secret"
        not in serialized
    )

    assert (
        "internal credential detail"
        not in serialized
    )


def test_auth_backend_unavailable_emits_event(
    monkeypatch,
):
    events = []

    async def fake_authenticate(
        token,
    ):
        raise AuthenticationUnavailableError(
            "database internals"
        )

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    monkeypatch.setattr(
        dependencies,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies
            .require_principal_context(
                authorization=(
                    "Bearer secret-token"
                )
            )
        )

    assert (
        exc_info.value.status_code
        == 503
    )

    assert events == [
        {
            "event_type": (
                "auth.unavailable"
            ),
            "outcome": "unavailable",
            "reason_code": (
                "authentication_backend_unavailable"
            ),
            "metadata": {
                "status_code": 503,
            },
        }
    ]

    assert (
        "database internals"
        not in repr(
            events
        )
    )


def test_rate_limit_denied_emits_safe_event(
    monkeypatch,
):
    events = []

    async def fake_consume_token(
        **kwargs,
    ):
        return RateLimitDecision(
            allowed=False,
            remaining=0,
            retry_after_seconds=7,
        )

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rate_limit_http,
        "consume_token",
        fake_consume_token,
    )

    monkeypatch.setattr(
        rate_limit_http,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            rate_limit_http
            .enforce_rate_limit(
                key=(
                    "rate-limit:"
                    "secret-internal-key"
                ),
                rate_per_minute=30,
                burst=5,
            )
        )

    assert (
        exc_info.value.status_code
        == 429
    )

    assert events == [
        {
            "event_type": (
                "rate_limit.denied"
            ),
            "outcome": "denied",
            "reason_code": (
                "rate_limit_exceeded"
            ),
            "metadata": {
                "status_code": 429,
                "retry_after_seconds": 7,
            },
        }
    ]

    assert (
        "secret-internal-key"
        not in repr(
            events
        )
    )


def test_rate_limit_unavailable_emits_safe_event(
    monkeypatch,
):
    events = []

    async def fake_consume_token(
        **kwargs,
    ):
        raise RateLimitUnavailableError(
            "redis internals"
        )

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rate_limit_http,
        "consume_token",
        fake_consume_token,
    )

    monkeypatch.setattr(
        rate_limit_http,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            rate_limit_http
            .enforce_rate_limit(
                key=(
                    "rate-limit:"
                    "secret-internal-key"
                ),
                rate_per_minute=30,
                burst=5,
            )
        )

    assert (
        exc_info.value.status_code
        == 503
    )

    assert events == [
        {
            "event_type": (
                "rate_limit.unavailable"
            ),
            "outcome": "unavailable",
            "reason_code": (
                "rate_limit_backend_unavailable"
            ),
            "metadata": {
                "status_code": 503,
            },
        }
    ]

    serialized = repr(
        events
    )

    assert (
        "secret-internal-key"
        not in serialized
    )

    assert (
        "redis internals"
        not in serialized
    )


def test_allowed_rate_limit_does_not_emit_event(
    monkeypatch,
):
    events = []

    async def fake_consume_token(
        **kwargs,
    ):
        return RateLimitDecision(
            allowed=True,
            remaining=4,
            retry_after_seconds=0,
        )

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rate_limit_http,
        "consume_token",
        fake_consume_token,
    )

    monkeypatch.setattr(
        rate_limit_http,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    result = asyncio.run(
        rate_limit_http
        .enforce_rate_limit(
            key="rate-limit:test",
            rate_per_minute=30,
            burst=5,
        )
    )

    assert result.allowed is True
    assert events == []
