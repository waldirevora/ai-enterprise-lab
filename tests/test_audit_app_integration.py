from fastapi.testclient import (
    TestClient,
)

from app.main import app


client = TestClient(
    app
)


def test_real_app_returns_request_id():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id
    assert len(request_id) == 32


def test_real_app_does_not_trust_client_request_id():
    response = client.get(
        "/health",
        headers={
            "X-Request-ID": (
                "client-controlled-id"
            )
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "X-Request-ID"
        ]
        != "client-controlled-id"
    )


def test_real_app_generates_unique_request_ids():
    first = client.get(
        "/health"
    )

    second = client.get(
        "/health"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        first.headers[
            "X-Request-ID"
        ]
        != second.headers[
            "X-Request-ID"
        ]
    )
