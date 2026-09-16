import pytest
from fastapi.testclient import TestClient

from app.access.context import PrincipalContext
from app.access.dependencies import (
    require_principal_context,
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
from app.api import rag as rag_api
from app.main import app
from app.rag.context_builder import RagContext
from app.rag.retrieval import RagSearchResult
from app.rag.service import RagGenerationResult
from app.schemas import GenerateResponse


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def stub_unit_access_grants(
    monkeypatch,
):
    async def fake_load_unit_access_grants(
        context,
    ):
        return ()

    monkeypatch.setattr(
        rag_api,
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
            referenced_unit_ids=frozenset(),
            unit_grants=unit_grants,
        )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )


def make_context(
    *,
    organization_id: int = 42,
    max_classification: str = "internal",
) -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=organization_id,
        organization_slug="empresa-a",
        principal_kind="service",
        role="service",
        max_classification=max_classification,
    )


def make_result(
    *,
    classification: str = "internal",
) -> RagGenerationResult:
    retrieved = RagSearchResult(
        chunk_id=10,
        document_id=5,
        title="Documento Autorizado",
        source="authenticated-test",
        source_uri=None,
        classification=classification,
        chunk_index=0,
        content="CONTEUDO_AUTORIZADO",
        metadata={},
        similarity=0.93,
    )

    context = RagContext(
        text="contexto autorizado",
        chunks_used=1,
        characters_used=18,
        effective_classification=(
            classification
        ),
        document_ids=(5,),
    )

    generation = GenerateResponse(
        provider="local_fast",
        backend="ollama",
        model="qwen2.5-coder:3b",
        response="AUTH_RAG_OK",
        prompt_tokens=25,
        generated_tokens=6,
        total_duration_ms=100.0,
    )

    return RagGenerationResult(
        generation=generation,
        retrieved_chunks=(retrieved,),
        context=context,
        effective_classification=(
            classification
        ),
    )


def test_authenticated_rag_requires_credentials():
    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API credential."
    }


def test_authenticated_rag_uses_principal_context(
    monkeypatch,
):
    context = make_context(
        organization_id=42,
        max_classification="internal",
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    captured = {}

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_result(
            classification="internal",
        )

    async def should_not_resolve_public_org():
        raise AssertionError(
            "Authenticated RAG must not use "
            "the public default organization."
        )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        should_not_resolve_public_org,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "Pergunta interna",
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
        == context.principal_id
    )

    assert (
        captured["principal_id"]
        == 10
    )

    assert (
        captured["question_classification"]
        == "internal"
    )

    assert (
        captured["allowed_classifications"]
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )

    assert captured["unit_grants"] == ()

    assert (
        response.json()["answer"]
        == "AUTH_RAG_OK"
    )


def test_confidential_context_allows_all_levels(
    monkeypatch,
):
    context = make_context(
        organization_id=77,
        max_classification="confidential",
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    captured = {}

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_result(
            classification="confidential",
        )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "Pergunta confidencial",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert (
        captured["organization_id"]
        == 77
    )

    assert (
        captured["principal_id"]
        == context.principal_id
    )

    assert (
        captured["principal_id"]
        == 10
    )

    assert (
        captured["question_classification"]
        == "confidential"
    )

    assert (
        captured["allowed_classifications"]
        == frozenset(
            {
                "public",
                "internal",
                "confidential",
            }
        )
    )

    assert captured["unit_grants"] == ()


def test_authenticated_client_cannot_choose_authority(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "teste",

            #
            # O cliente tenta escolher
            # sua própria autoridade.
            #
            # Todos estes campos devem
            # ser rejeitados pelo schema.
            #
            "principal_id": 999,
            "organization_id": 999,
            "allowed_classifications": [
                "confidential"
            ],
            "organizational_unit_id": 888,
            "unit_grants": [
                {
                    "organizational_unit_id": 888,
                }
            ],
        },
    )

    assert response.status_code == 422


def test_authenticated_rag_forwards_unit_grants(
    monkeypatch,
):
    context = make_context(
        organization_id=42,
        max_classification="internal",
    )

    grant = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification="internal",
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    captured = {}

    async def fake_load_unit_access_grants(
        received_context,
    ):
        assert received_context is context

        return (
            grant,
        )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_result(
            classification="internal",
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_unit_access_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "Pergunta Financeiro",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert captured["unit_grants"] == (
        grant,
    )

    assert (
        captured["organization_id"]
        == 42
    )

    assert (
        captured["principal_id"]
        == context.principal_id
    )


def test_authorized_explicit_unit_restricts_grants(
    monkeypatch,
):
    context = make_context()

    financeiro = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification="internal",
    )

    rh = UnitAccessGrant(
        organizational_unit_id=200,
        unit_slug="rh",
        unit_name="RH",
        role="member",
        effective_max_classification="internal",
    )

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    async def fake_load_unit_access_grants(
        received_context,
    ):
        assert received_context is context

        return (
            financeiro,
            rh,
        )

    async def fake_resolve_unit_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        assert unit_grants == (
            financeiro,
            rh,
        )

        return UnitScopeDecision(
            referenced_unit_ids=frozenset(
                {
                    100,
                }
            ),
            unit_grants=(
                financeiro,
            ),
        )

    captured = {}

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_result(
            classification="internal",
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_unit_access_grants,
    )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": (
                "Qual é o código do Financeiro?"
            ),
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert captured["unit_grants"] == (
        financeiro,
    )

    assert (
        captured["principal_id"]
        == context.principal_id
    )


def test_unauthorized_unit_scope_returns_404_before_rag(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    async def fake_resolve_unit_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        raise UnitScopeDeniedError(
            "internal authorization detail"
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "RAG generation must not run "
            "after unit scope denial."
        )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        should_not_generate,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": (
                "Qual é o código do RH?"
            ),
            "provider": "local_fast",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No authorized RAG context was found."
        )
    }

    assert (
        "internal authorization detail"
        not in response.text
    )


def test_zero_grants_still_runs_scope_guard(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    captured = {}

    async def fake_resolve_unit_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        captured["unit_grants"] = (
            unit_grants
        )

        raise UnitScopeDeniedError(
            "denied"
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "RAG generation must not run."
        )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        should_not_generate,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "RH",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 404

    assert captured["unit_grants"] == ()


def test_unit_scope_unavailable_returns_503(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    async def fake_resolve_unit_scope(
        *,
        context,
        question,
        unit_grants,
    ):
        raise UnitScopeUnavailableError(
            "database detail"
        )

    monkeypatch.setattr(
        rag_api,
        "resolve_unit_scope",
        fake_resolve_unit_scope,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "teste",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit scope service unavailable."
        )
    }

    assert (
        "database detail"
        not in response.text
    )


def test_unit_authorization_unavailable_returns_503(
    monkeypatch,
):
    context = make_context()

    async def fake_dependency():
        return context

    app.dependency_overrides[
        require_principal_context
    ] = fake_dependency

    async def fake_load_unit_access_grants(
        received_context,
    ):
        raise UnitGrantUnavailableError(
            "database detail"
        )

    monkeypatch.setattr(
        rag_api,
        "load_unit_access_grants",
        fake_load_unit_access_grants,
    )

    response = client.post(
        "/v1/rag/generate-authenticated",
        json={
            "question": "teste",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Unit authorization service unavailable."
        )
    }

    assert (
        "database detail"
        not in response.text
    )