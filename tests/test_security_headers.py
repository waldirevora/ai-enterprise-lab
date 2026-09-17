from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_security_headers_are_added():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )

    assert (
        response.headers[
            "referrer-policy"
        ]
        == "no-referrer"
    )

    assert (
        response.headers[
            "permissions-policy"
        ]
        == (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )
    )


def test_security_headers_are_added_to_rejected_host():
    response = client.get(
        "/health",
        headers={
            "host": "evil.example",
        },
    )

    assert response.status_code == 400

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )


def test_hsts_is_not_enabled_before_tls_contract():
    response = client.get(
        "/health"
    )

    assert (
        "strict-transport-security"
        not in response.headers
    )
