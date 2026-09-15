import pytest
from fastapi.testclient import TestClient

from app.access.context import PrincipalContext
from app.access.dependencies import (
    require_principal_context,
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
            "organization_id": 999,
            "allowed_classifications": [
                "confidential"
            ],
        },
    )

    assert response.status_code == 422