from fastapi import (
    FastAPI,
    Request,
)
from fastapi.testclient import (
    TestClient,
)

from app.audit.context import (
    get_request_id,
)
from app.audit.middleware import (
    AuditRequestContextMiddleware,
)


def make_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        AuditRequestContextMiddleware
    )

    @app.get("/probe")
    async def probe(
        request: Request,
    ):
        return {
            "context_request_id": (
                get_request_id()
            ),
            "state_request_id": (
                request.state.request_id
            ),
        }

    return app


def test_request_id_is_available_and_returned():
    client = TestClient(
        make_app()
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 200

    request_id = (
        response.headers[
            "X-Request-ID"
        ]
    )

    body = response.json()

    assert request_id

    assert (
        body[
            "context_request_id"
        ]
        == request_id
    )

    assert (
        body[
            "state_request_id"
        ]
        == request_id
    )


def test_client_request_id_is_not_trusted():
    client = TestClient(
        make_app()
    )

    response = client.get(
        "/probe",
        headers={
            "X-Request-ID": (
                "client-controlled-id"
            ),
        },
    )

    server_request_id = (
        response.headers[
            "X-Request-ID"
        ]
    )

    assert (
        server_request_id
        != "client-controlled-id"
    )


def test_each_request_gets_a_new_request_id():
    client = TestClient(
        make_app()
    )

    first = client.get(
        "/probe"
    )

    second = client.get(
        "/probe"
    )

    assert (
        first.headers[
            "X-Request-ID"
        ]
        != second.headers[
            "X-Request-ID"
        ]
    )

    assert get_request_id() is None
