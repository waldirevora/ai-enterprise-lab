from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)

from app.access import dependencies
from app.access.context import (
    PrincipalContext,
)
from app.api import rag
from app.main import app as gateway_app
import app.main as gateway_main
from app.rate_limit.origin import (
    RateLimitOriginError,
)


def expected_event():
    return {
        "event_type": (
            "rate_limit.unavailable"
        ),
        "outcome": "unavailable",
        "reason_code": (
            "rate_limit_origin_unavailable"
        ),
        "metadata": {
            "status_code": 503,
        },
    }


def test_public_generate_origin_failure_is_audited(
    monkeypatch,
):
    events = []

    def fail_origin(
        **kwargs,
    ):
        raise RateLimitOriginError(
            "raw origin detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        gateway_main,
        "build_origin_key",
        fail_origin,
    )

    monkeypatch.setattr(
        gateway_main,
        "emit_audit_event",
        capture_event,
    )

    client = TestClient(
        gateway_app
    )

    response = client.post(
        "/v1/generate",
        json={
            "prompt": "test",
        },
        headers={
            "X-Forwarded-For": (
                "203.0.113.10"
            ),
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service unavailable."
        )
    }

    assert events == [
        expected_event()
    ]

    serialized = repr(
        events
    )

    assert (
        "raw origin detail"
        not in serialized
    )

    assert (
        "203.0.113.10"
        not in serialized
    )


def test_public_rag_origin_failure_is_audited(
    monkeypatch,
):
    events = []

    def fail_origin(
        **kwargs,
    ):
        raise RateLimitOriginError(
            "raw rag origin detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag,
        "build_origin_key",
        fail_origin,
    )

    monkeypatch.setattr(
        rag,
        "emit_audit_event",
        capture_event,
    )

    client = TestClient(
        gateway_app
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "test",
        },
        headers={
            "X-Forwarded-For": (
                "198.51.100.20"
            ),
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service unavailable."
        )
    }

    assert events == [
        expected_event()
    ]

    serialized = repr(
        events
    )

    assert (
        "raw rag origin detail"
        not in serialized
    )

    assert (
        "198.51.100.20"
        not in serialized
    )


def test_authenticated_preauth_origin_failure_is_audited(
    monkeypatch,
):
    events = []

    def fail_origin(
        **kwargs,
    ):
        raise RateLimitOriginError(
            "raw auth origin detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        dependencies,
        "build_origin_key",
        fail_origin,
    )

    monkeypatch.setattr(
        dependencies,
        "emit_audit_event",
        capture_event,
    )

    test_app = FastAPI()

    @test_app.get(
        "/protected"
    )
    async def protected(
        context: PrincipalContext = Depends(
            dependencies
            .require_rate_limited_principal_context
        ),
    ):
        return {
            "principal_id": (
                context.principal_id
            )
        }

    client = TestClient(
        test_app
    )

    response = client.get(
        "/protected",
        headers={
            "Authorization": (
                "Bearer secret-token"
            ),
            "X-Forwarded-For": (
                "192.0.2.30"
            ),
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service unavailable."
        )
    }

    assert events == [
        expected_event()
    ]

    serialized = repr(
        events
    )

    assert (
        "secret-token"
        not in serialized
    )

    assert (
        "raw auth origin detail"
        not in serialized
    )

    assert (
        "192.0.2.30"
        not in serialized
    )
