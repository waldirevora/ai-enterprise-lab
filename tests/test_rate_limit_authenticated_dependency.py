from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
)
from fastapi.testclient import TestClient

from app.access import dependencies
from app.access.context import PrincipalContext
from app.core.config import settings
from app.rate_limit.models import (
    RateLimitDecision,
)


app = FastAPI()


@app.get("/protected-rate-limited")
async def protected_rate_limited(
    context: PrincipalContext = Depends(
        dependencies
        .require_rate_limited_principal_context
    ),
):
    return {
        "principal_id": (
            context.principal_id
        ),
        "organization_id": (
            context.organization_id
        ),
    }


client = TestClient(app)


def make_context() -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=20,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification="internal",
    )


def test_authenticated_limits_execute_in_security_order(
    monkeypatch,
):
    context = make_context()

    events = []

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        events.append(
            (
                "rate-limit",
                kwargs,
            )
        )

        return RateLimitDecision(
            allowed=True,
            remaining=10,
            retry_after_seconds=0,
        )

    async def fake_authenticate(
        token,
    ):
        events.append(
            (
                "authenticate",
                token,
            )
        )

        return context

    monkeypatch.setattr(
        dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    response = client.get(
        "/protected-rate-limited",
        headers={
            "Authorization": (
                "Bearer ael_test_token"
            ),
        },
    )

    assert response.status_code == 200

    assert len(events) == 3

    assert events[0][0] == "rate-limit"

    preauth = events[0][1]

    assert (
        preauth["key"].startswith(
            "rate-limit:auth-preauth:"
        )
    )

    assert (
        preauth["rate_per_minute"]
        == settings
        .rate_limit_auth_preauth_per_minute
    )

    assert (
        preauth["burst"]
        == settings
        .rate_limit_auth_preauth_burst
    )

    assert events[1] == (
        "authenticate",
        "ael_test_token",
    )

    assert events[2][0] == "rate-limit"

    principal = events[2][1]

    assert principal["key"] == (
        "rate-limit:principal:20:10"
    )

    assert (
        principal["rate_per_minute"]
        == settings
        .rate_limit_auth_principal_per_minute
    )

    assert (
        principal["burst"]
        == settings
        .rate_limit_auth_principal_burst
    )

    assert response.json() == {
        "principal_id": 10,
        "organization_id": 20,
    }


def test_preauth_429_blocks_authentication(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={
                "Retry-After": "8",
            },
        )

    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication must not run "
            "after pre-auth denial."
        )

    monkeypatch.setattr(
        dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    response = client.get(
        "/protected-rate-limited",
        headers={
            "Authorization": (
                "Bearer invalid-token"
            ),
        },
    )

    assert response.status_code == 429

    assert response.json() == {
        "detail": "Rate limit exceeded."
    }

    assert (
        response.headers["Retry-After"]
        == "8"
    )


def test_preauth_503_blocks_authentication(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Rate limit service unavailable."
            ),
        )

    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication must not run "
            "when the rate limit backend "
            "is unavailable."
        )

    monkeypatch.setattr(
        dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    response = client.get(
        "/protected-rate-limited",
        headers={
            "Authorization": (
                "Bearer ael_test_token"
            ),
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service unavailable."
        )
    }


def test_postauth_429_happens_after_authentication(
    monkeypatch,
):
    context = make_context()

    calls = {
        "rate_limit": 0,
        "authenticated": False,
    }

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        calls["rate_limit"] += 1

        if calls["rate_limit"] == 1:
            return RateLimitDecision(
                allowed=True,
                remaining=9,
                retry_after_seconds=0,
            )

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={
                "Retry-After": "3",
            },
        )

    async def fake_authenticate(
        token,
    ):
        calls["authenticated"] = True

        return context

    monkeypatch.setattr(
        dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    response = client.get(
        "/protected-rate-limited",
        headers={
            "Authorization": (
                "Bearer ael_valid_token"
            ),
        },
    )

    assert calls["authenticated"] is True
    assert calls["rate_limit"] == 2

    assert response.status_code == 429

    assert (
        response.headers["Retry-After"]
        == "3"
    )


def test_missing_credential_preserves_401_after_preauth(
    monkeypatch,
):
    calls = {
        "rate_limit": 0,
    }

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        calls["rate_limit"] += 1

        return RateLimitDecision(
            allowed=True,
            remaining=9,
            retry_after_seconds=0,
        )

    async def should_not_authenticate(
        token,
    ):
        raise AssertionError(
            "Authentication must not run "
            "without a Bearer token."
        )

    monkeypatch.setattr(
        dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        should_not_authenticate,
    )

    response = client.get(
        "/protected-rate-limited"
    )

    assert calls["rate_limit"] == 1

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API credential."
    }

    assert (
        response.headers[
            "www-authenticate"
        ]
        == "Bearer"
    )