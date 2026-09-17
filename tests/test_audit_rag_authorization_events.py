from types import SimpleNamespace

import pytest
from fastapi.testclient import (
    TestClient,
)

from app.access.context import (
    PrincipalContext,
)
from app.access.dependencies import (
    require_rate_limited_principal_context,
)
from app.access.unit_grants import (
    UnitGrantUnavailableError,
)
from app.access.unit_scope import (
    UnitScopeDecision,
    UnitScopeDeniedError,
    UnitScopeUnavailableError,
)
from app.api import rag as rag_api
from app.main import app
from app.rag.service import (
    RagServiceError,
)


client = TestClient(
    app
)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


def make_context() -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=42,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification="internal",
    )


def install_context():
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    return context


def test_unit_scope_denied_emits_safe_event(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context
        return ()

    async def fake_resolve_scope(
        **kwargs,
    ):
        raise UnitScopeDeniedError(
            "secret unit authorization detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No authorized RAG context was found."
        )
    }

    assert events == [
        {
            "event_type": (
                "authorization.unit_scope_denied"
            ),
            "outcome": "denied",
            "organization_id": 42,
            "principal_id": 10,
            "reason_code": (
                "unit_scope_denied"
            ),
            "metadata": {
                "status_code": 404,
            },
        }
    ]

    serialized = repr(
        events
    )

    assert (
        "SECRET_QUESTION"
        not in serialized
    )

    assert (
        "secret unit authorization detail"
        not in serialized
    )


def test_unit_scope_unavailable_emits_safe_event(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context
        return ()

    async def fake_resolve_scope(
        **kwargs,
    ):
        raise UnitScopeUnavailableError(
            "database internal detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit scope service unavailable."
        )
    }

    assert events == [
        {
            "event_type": (
                "authorization.unit_scope_unavailable"
            ),
            "outcome": "unavailable",
            "organization_id": 42,
            "principal_id": 10,
            "reason_code": (
                "unit_scope_backend_unavailable"
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
        "SECRET_QUESTION"
        not in serialized
    )

    assert (
        "database internal detail"
        not in serialized
    )


def test_unit_grants_unavailable_emits_safe_event(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context

        raise UnitGrantUnavailableError(
            "database grant detail"
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit authorization service unavailable."
        )
    }

    assert events == [
        {
            "event_type": (
                "authorization.unit_grants_unavailable"
            ),
            "outcome": "unavailable",
            "organization_id": 42,
            "principal_id": 10,
            "reason_code": (
                "unit_grants_backend_unavailable"
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
        "SECRET_QUESTION"
        not in serialized
    )

    assert (
        "database grant detail"
        not in serialized
    )


def test_authorized_context_not_found_emits_safe_event(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context
        return ()

    async def fake_resolve_scope(
        **kwargs,
    ):
        return UnitScopeDecision(
            referenced_unit_ids=frozenset(),
            unit_grants=(),
        )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        raise RagServiceError(
            "No authorized RAG context was found."
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No authorized RAG context was found."
        )
    }

    assert events == [
        {
            "event_type": (
                "rag.authorized_context_not_found"
            ),
            "outcome": "failure",
            "organization_id": 42,
            "principal_id": 10,
            "reason_code": (
                "authorized_context_not_found"
            ),
            "metadata": {
                "status_code": 404,
            },
        }
    ]

    assert (
        "SECRET_QUESTION"
        not in repr(
            events
        )
    )


def test_other_rag_service_error_is_not_misclassified(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context
        return ()

    async def fake_resolve_scope(
        **kwargs,
    ):
        return UnitScopeDecision(
            referenced_unit_ids=frozenset(),
            unit_grants=(),
        )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        raise RagServiceError(
            "Authorized RAG context is empty."
        )

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "RAG service unavailable."
    }

    assert (
        "Authorized RAG context is empty."
        not in response.text
    )

    assert events == []

def test_authenticated_rag_success_emits_safe_event(
    monkeypatch,
):
    context = install_context()
    events = []

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context
        return ()

    async def fake_resolve_scope(
        **kwargs,
    ):
        return UnitScopeDecision(
            referenced_unit_ids=frozenset(),
            unit_grants=(),
        )

    result = SimpleNamespace(
        generation=SimpleNamespace(
            provider="local_fast",
        ),
        effective_classification=(
            "internal"
        ),
        retrieved_chunks=(
            object(),
            object(),
        ),
    )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        return result

    def fake_build_response(
        received_result,
    ):
        assert received_result is result

        return {
            "answer": "AUTH_RAG_OK",
            "provider": "local_fast",
            "backend": "ollama",
            "model": "test-model",
            "effective_classification": (
                "internal"
            ),
            "citations": [],
            "prompt_tokens": 1,
            "generated_tokens": 1,
            "reasoning_tokens": None,
            "total_duration_ms": 1.0,
            "pricing_tier": None,
            "estimated_cost_usd": None,
        }

    def capture_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    monkeypatch.setattr(
        rag_api,
        "_build_response",
        fake_build_response,
    )

    monkeypatch.setattr(
        rag_api,
        "emit_audit_event",
        capture_event,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "SECRET_QUESTION",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert events == [
        {
            "event_type": (
                "rag.authenticated.success"
            ),
            "outcome": "success",
            "organization_id": 42,
            "principal_id": 10,
            "provider": "local_fast",
            "classification": "internal",
            "reason_code": (
                "authenticated_rag_completed"
            ),
            "metadata": {
                "status_code": 200,
                "retrieved_chunks": 2,
            },
        }
    ]

    serialized = repr(
        events
    )

    assert (
        "SECRET_QUESTION"
        not in serialized
    )
