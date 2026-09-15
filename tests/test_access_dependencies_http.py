from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.access import dependencies
from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
)
from app.access.context import PrincipalContext


app = FastAPI()


@app.get("/protected")
async def protected_route(
    context: PrincipalContext = Depends(
        dependencies.require_principal_context
    ),
):
    return {
        "principal_id": context.principal_id,
        "organization_id": context.organization_id,
        "organization_slug": context.organization_slug,
        "principal_kind": context.principal_kind,
        "role": context.role,
        "max_classification": (
            context.max_classification
        ),
        "allowed_classifications": sorted(
            context.allowed_classifications
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


def test_http_missing_authorization_returns_401():
    response = client.get(
        "/protected"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API credential."
    }

    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_http_valid_bearer_returns_context(
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

    response = client.get(
        "/protected",
        headers={
            "Authorization": (
                "Bearer ael_http_test_token"
            ),
        },
    )

    assert response.status_code == 200

    assert (
        captured["token"]
        == "ael_http_test_token"
    )

    assert response.json() == {
        "principal_id": 10,
        "organization_id": 20,
        "organization_slug": "empresa-a",
        "principal_kind": "service",
        "role": "service",
        "max_classification": "internal",
        "allowed_classifications": [
            "internal",
            "public",
        ],
    }


def test_http_invalid_api_key_returns_401(
    monkeypatch,
):
    async def fake_authenticate(
        token,
    ):
        raise AuthenticationError(
            "credential internally rejected"
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    response = client.get(
        "/protected",
        headers={
            "Authorization": (
                "Bearer ael_invalid_token"
            ),
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API credential."
    }

    assert (
        "credential internally rejected"
        not in response.text
    )


def test_http_authentication_unavailable_returns_503(
    monkeypatch,
):
    async def fake_authenticate(
        token,
    ):
        raise AuthenticationUnavailableError(
            "database connection failed"
        )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        fake_authenticate,
    )

    response = client.get(
        "/protected",
        headers={
            "Authorization": (
                "Bearer ael_test_token"
            ),
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Authentication service unavailable."
        )
    }

    assert (
        "database connection failed"
        not in response.text
    )