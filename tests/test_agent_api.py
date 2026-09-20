import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.access import (
    dependencies as access_dependencies,
)
from app.access.context import (
    PrincipalContext,
)
from app.access.dependencies import (
    require_rate_limited_principal_context,
)
from app.access.unit_grants import (
    UnitAccessGrant,
    UnitGrantUnavailableError,
)
from app.access.unit_scope import (
    UnitScopeDecision,
    UnitScopeDeniedError,
    UnitScopeUnavailableError,
)
from app.agents.schemas import (
    AgentRunResponse,
    AgentToolTrace,
)
from app.agents.service import (
    AgentNoContextError,
    AgentServiceError,
)
from app.api import agents as agents_api
from app.main import app
from app.rate_limit.models import (
    RateLimitDecision,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def allow_authenticated_rate_limit(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        return RateLimitDecision(
            allowed=True,
            remaining=999,
            retry_after_seconds=0,
        )

    monkeypatch.setattr(
        access_dependencies,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )


@pytest.fixture(autouse=True)
def stub_unit_access_grants(
    monkeypatch,
):
    async def fake_load_unit_access_grants(
        context,
    ):
        return ()

    monkeypatch.setattr(
        agents_api,
        "load_unit_access_grants",
        fake_load_unit_access_grants,
    )


@pytest.fixture(autouse=True)
def stub_unit_scope(
    monkeypatch,
):
    async def fake_resolve_unit_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        return UnitScopeDecision(
            referenced_unit_ids=(
                frozenset()
            ),
            unit_grants=unit_grants,
        )

    monkeypatch.setattr(
        agents_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )


def make_context(
    *,
    organization_id=42,
    max_classification="internal",
):
    return PrincipalContext(
        principal_id=10,
        organization_id=organization_id,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification=(
            max_classification
        ),
    )


def make_agent_response(
    *,
    classification="internal",
):
    return AgentRunResponse(
        answer="AGENT_OK",
        provider="local_fast",
        backend="ollama",
        model="test-model",
        effective_classification=(
            classification
        ),
        citations=[],
        tool_trace=[
            AgentToolTrace(
                name=(
                    "search_enterprise_knowledge"
                ),
                status="completed",
                chunks_used=1,
                characters_used=100,
            )
        ],
        steps_executed=2,
    )


def test_agent_api_requires_credentials():
    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API credential."
    }


def test_agent_api_uses_principal_context(
    monkeypatch,
):
    context = make_context(
        organization_id=42,
        max_classification="internal",
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    captured = {}

    async def fake_run_agent(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_agent_response()

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        fake_run_agent,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": (
                "Qual é a política?"
            ),
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert (
        captured["organization_id"]
        == 42
    )

    assert (
        captured["principal_id"]
        == 10
    )

    assert (
        captured[
            "question_classification"
        ]
        == "internal"
    )

    assert (
        captured[
            "allowed_classifications"
        ]
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )

    assert captured["unit_grants"] == ()

    assert (
        captured["request"].message
        == "Qual é a política?"
    )

    assert (
        response.json()["answer"]
        == "AGENT_OK"
    )


def test_agent_api_rejects_client_authority_fields():
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
            "organization_id": 999,
            "principal_id": 999,
            "allowed_classifications": [
                "confidential"
            ],
            "unit_grants": [],
            "tool": (
                "search_enterprise_knowledge"
            ),
            "tool_arguments": {},
            "system_prompt": "override",
            "context": "raw",
        },
    )

    assert response.status_code == 422


def test_agent_api_restricts_explicit_unit_scope(
    monkeypatch,
):
    context = make_context()

    financeiro = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification=(
            "internal"
        ),
    )

    rh = UnitAccessGrant(
        organizational_unit_id=200,
        unit_slug="rh",
        unit_name="RH",
        role="member",
        effective_max_classification=(
            "internal"
        ),
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def fake_load_grants(
        received_context,
    ):
        assert received_context is context

        return (
            financeiro,
            rh,
        )

    async def fake_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        assert question == (
            "Política do Financeiro"
        )

        assert unit_grants == (
            financeiro,
            rh,
        )

        return UnitScopeDecision(
            referenced_unit_ids=(
                frozenset(
                    {
                        100,
                    }
                )
            ),
            unit_grants=(
                financeiro,
            ),
        )

    captured = {}

    async def fake_run_agent(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_agent_response()

    monkeypatch.setattr(
        agents_api,
        "load_unit_access_grants",
        fake_load_grants,
    )

    monkeypatch.setattr(
        agents_api,
        "resolve_unit_scope",
        fake_scope,
    )

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        fake_run_agent,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": (
                "Política do Financeiro"
            ),
        },
    )

    assert response.status_code == 200

    assert captured["unit_grants"] == (
        financeiro,
    )


def test_agent_api_unit_scope_denial_is_generic(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def deny_scope(
        **kwargs,
    ):
        raise UnitScopeDeniedError(
            "PRIVATE_SCOPE_DETAIL"
        )

    async def should_not_run_agent(
        **kwargs,
    ):
        raise AssertionError(
            "Agent must not run after "
            "scope denial."
        )

    monkeypatch.setattr(
        agents_api,
        "resolve_unit_scope",
        deny_scope,
    )

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        should_not_run_agent,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "RH",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No authorized enterprise "
            "knowledge was found."
        )
    }

    assert (
        "PRIVATE_SCOPE_DETAIL"
        not in response.text
    )


def test_agent_api_unit_scope_unavailable(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def unavailable_scope(
        **kwargs,
    ):
        raise UnitScopeUnavailableError(
            "PRIVATE_SCOPE_BACKEND"
        )

    monkeypatch.setattr(
        agents_api,
        "resolve_unit_scope",
        unavailable_scope,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit scope service "
            "unavailable."
        )
    }

    assert (
        "PRIVATE_SCOPE_BACKEND"
        not in response.text
    )


def test_agent_api_unit_grants_unavailable(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def unavailable_grants(
        context,
    ):
        raise UnitGrantUnavailableError(
            "PRIVATE_GRANT_BACKEND"
        )

    monkeypatch.setattr(
        agents_api,
        "load_unit_access_grants",
        unavailable_grants,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit authorization "
            "service unavailable."
        )
    }

    assert (
        "PRIVATE_GRANT_BACKEND"
        not in response.text
    )


def test_agent_api_no_context_returns_generic_404(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def no_context(
        **kwargs,
    ):
        raise AgentNoContextError(
            "PRIVATE_CONTEXT_DETAIL"
        )

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        no_context,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No authorized enterprise "
            "knowledge was found."
        )
    }

    assert (
        "PRIVATE_CONTEXT_DETAIL"
        not in response.text
    )


def test_agent_api_service_failure_is_sanitized(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def unavailable_agent(
        **kwargs,
    ):
        raise AgentServiceError(
            "PRIVATE_AGENT_DETAIL"
        )

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        unavailable_agent,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Agent service unavailable."
        )
    }

    assert (
        "PRIVATE_AGENT_DETAIL"
        not in response.text
    )


def test_agent_api_preserves_provider_policy_http_exception(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_rate_limited_principal_context
    ] = fake_dependency

    async def provider_rejected(
        **kwargs,
    ):
        raise HTTPException(
            status_code=403,
            detail="Provider blocked.",
        )

    monkeypatch.setattr(
        agents_api,
        "run_enterprise_knowledge_agent",
        provider_rejected,
    )

    response = client.post(
        (
            "/v1/agents/"
            "enterprise-knowledge/run"
        ),
        json={
            "message": "teste",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Provider blocked."
    }
