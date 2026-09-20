from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.observability.middleware import (
    HttpMetricsMiddleware,
)


def _build_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        HttpMetricsMiddleware
    )

    @app.get("/items/{item_id}")
    def read_item(
        item_id: str,
    ) -> dict[str, str]:
        return {
            "item_id": item_id,
        }

    @app.get("/failure")
    def failure() -> None:
        raise RuntimeError(
            "intentional test failure"
        )

    return app


def test_http_metrics_use_route_template():
    app = _build_app()

    client = TestClient(app)

    response = client.get(
        "/items/private-value-123"
    )

    assert response.status_code == 200

    payload = generate_latest(
        METRICS_REGISTRY
    ).decode()

    assert (
        'route="/items/{item_id}"'
        in payload
    )

    assert (
        "private-value-123"
        not in payload
    )

    assert 'status_class="2xx"' in payload


def test_unmatched_path_is_bounded():
    app = _build_app()

    client = TestClient(app)

    response = client.get(
        "/unknown/private-value-456"
    )

    assert response.status_code == 404

    payload = generate_latest(
        METRICS_REGISTRY
    ).decode()

    assert 'route="__unmatched__"' in payload

    assert (
        "private-value-456"
        not in payload
    )

    assert 'status_class="4xx"' in payload


def test_exception_records_5xx_without_exception_text():
    app = _build_app()

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = client.get(
        "/failure"
    )

    assert response.status_code == 500

    payload = generate_latest(
        METRICS_REGISTRY
    ).decode()

    assert 'route="/failure"' in payload
    assert 'status_class="5xx"' in payload

    assert (
        "intentional test failure"
        not in payload
    )
