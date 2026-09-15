import asyncio

import pytest
from fastapi import HTTPException

from app.access import dependencies
from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
)
from app.access.context import PrincipalContext


def make_context() -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=20,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification="internal",
    )


def test_missing_authorization_header_is_rejected(
    monkeypatch,
):
    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication should not run."
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization=None,
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert (
        exc_info.value.detail
        == "Invalid API credential."
    )

    assert (
        exc_info.value.headers[
            "WWW-Authenticate"
        ]
        == "Bearer"
    )


def test_non_bearer_scheme_is_rejected(
    monkeypatch,
):
    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication should not run."
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization=(
                    "Basic abc123"
                ),
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_missing_bearer_token_is_rejected(
    monkeypatch,
):
    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication should not run."
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization="Bearer",
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_malformed_authorization_header_is_rejected(
    monkeypatch,
):
    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication should not run."
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization=(
                    "Bearer token extra"
                ),
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_invalid_api_key_returns_401(
    monkeypatch,
):
    async def fake_authenticate(
        token,
    ):
        raise AuthenticationError(
            "internal authentication detail"
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization=(
                    "Bearer ael_testtoken"
                ),
            )
        )

    assert (
        exc_info.value.status_code
        == 401
    )

    assert (
        exc_info.value.detail
        == "Invalid API credential."
    )

    assert (
        "internal authentication detail"
        not in exc_info.value.detail
    )


def test_authentication_unavailable_returns_503(
    monkeypatch,
):
    async def fake_authenticate(
        token,
    ):
        raise AuthenticationUnavailableError(
            "database unavailable"
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            dependencies.require_principal_context(
                authorization=(
                    "Bearer ael_testtoken"
                ),
            )
        )

    assert (
        exc_info.value.status_code
        == 503
    )

    assert (
        exc_info.value.detail
        == "Authentication service unavailable."
    )

    assert (
        "database unavailable"
        not in exc_info.value.detail
    )


def test_valid_api_key_returns_principal_context(
    monkeypatch,
):
    expected_context = make_context()

    captured = {}

    async def fake_authenticate(
        token,
    ):
        captured["token"] = token

        return expected_context

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    context = asyncio.run(
        dependencies.require_principal_context(
            authorization=(
                "Bearer ael_testtoken"
            ),
        )
    )

    assert context is expected_context

    assert (
        captured["token"]
        == "ael_testtoken"
    )

    assert (
        context.organization_id
        == 20
    )

    assert (
        context.allowed_classifications
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )