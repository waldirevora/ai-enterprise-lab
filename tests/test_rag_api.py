import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import rag as rag_api
from app.core.config import settings
from app.main import app
from app.rate_limit.models import (
    RateLimitDecision,
)
from app.rag.context_builder import RagContext
from app.rag.retrieval import RagSearchResult
from app.rag.service import (
    RagGenerationResult,
    RagServiceError,
)
from app.schemas import GenerateResponse


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_default_organization(
    monkeypatch,
):
    async def fake_resolve():
        return 1

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        fake_resolve,
    )


@pytest.fixture(autouse=True)
def allow_public_rag_rate_limit(
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
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )


def make_result() -> RagGenerationResult:
    retrieved = RagSearchResult(
        chunk_id=10,
        document_id=1,
        title="Documento Publico",
        source="public-test",
        source_uri=None,
        classification="public",
        chunk_index=0,
        content="CONTEUDO_INTERNO_DO_CHUNK",
        metadata={},
        similarity=0.91,
    )

    context = RagContext(
        text="contexto",
        chunks_used=1,
        characters_used=8,
        effective_classification="public",
        document_ids=(1,),
    )

    generation = GenerateResponse(
        provider="local_fast",
        backend="ollama",
        model="qwen2.5-coder:3b",
        response="RAG_API_OK",
        prompt_tokens=20,
        generated_tokens=5,
        total_duration_ms=100.0,
    )

    return RagGenerationResult(
        generation=generation,
        retrieved_chunks=(retrieved,),
        context=context,
        effective_classification="public",
    )


def test_rag_endpoint_is_public_only(
    monkeypatch,
):
    captured = {}

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_result()

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "Pergunta publica",
            "provider": "local_fast",
        },
    )

    assert response.status_code == 200

    assert (
        captured["organization_id"]
        == 1
    )

    assert (
        captured["question_classification"]
        == "public"
    )

    assert (
        captured["allowed_classifications"]
        == {"public"}
    )


def test_client_cannot_choose_allowed_classifications():
    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
            "allowed_classifications": [
                "confidential"
            ],
        },
    )

    assert response.status_code == 422


def test_client_cannot_choose_organization():
    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
            "organization_id": 999,
        },
    )

    assert response.status_code == 422


def test_rag_response_does_not_expose_chunk_content(
    monkeypatch,
):
    async def fake_generate_rag_answer(
        **kwargs,
    ):
        return make_result()

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["answer"] == "RAG_API_OK"

    assert len(
        body["citations"]
    ) == 1

    assert body["citations"][0] == {
        "title": "Documento Publico",
        "source": "public-test",
    }

    assert (
        "CONTEUDO_INTERNO_DO_CHUNK"
        not in response.text
    )

    for key in (
        "document_id",
        "classification",
        "chunk_index",
        "similarity",
        "source_uri",
        "content",
        "metadata",
        "embedding",
    ):
        assert key not in body["citations"][0]


def test_no_authorized_context_returns_404(
    monkeypatch,
):
    async def fake_generate_rag_answer(
        **kwargs,
    ):
        raise RagServiceError(
            "No authorized RAG context was found."
        )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "No authorized RAG context was found."
    )


def test_policy_http_exception_is_preserved(
    monkeypatch,
):
    async def fake_generate_rag_answer(
        **kwargs,
    ):
        raise HTTPException(
            status_code=403,
            detail="Provider blocked.",
        )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Provider blocked."
    )


def test_unavailable_default_organization_returns_503(
    monkeypatch,
):
    async def fake_resolve():
        raise HTTPException(
            status_code=503,
            detail="RAG organization is unavailable.",
        )

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        fake_resolve,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 503

    assert response.json()["detail"] == (
        "RAG organization is unavailable."
    )


def test_public_rag_forwards_rate_limit_policy(
    monkeypatch,
):
    captured = {}

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return RateLimitDecision(
            allowed=True,
            remaining=2,
            retry_after_seconds=0,
        )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        return make_result()

    monkeypatch.setattr(
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 200

    assert (
        captured["key"].startswith(
            "rate-limit:public-rag:"
        )
    )

    assert (
        captured["rate_per_minute"]
        == settings
        .rate_limit_public_rag_per_minute
    )

    assert (
        captured["burst"]
        == settings
        .rate_limit_public_rag_burst
    )


def test_public_rag_rate_limit_returns_429_before_rag(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={
                "Retry-After": "5",
            },
        )

    async def should_not_resolve():
        raise AssertionError(
            "Organization resolution must not run "
            "after rate limit denial."
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "RAG generation must not run "
            "after rate limit denial."
        )

    monkeypatch.setattr(
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        should_not_resolve,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        should_not_generate,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 429

    assert response.json() == {
        "detail": "Rate limit exceeded."
    }

    assert (
        response.headers["Retry-After"]
        == "5"
    )


def test_public_rag_rate_limit_unavailable_returns_503_before_rag(
    monkeypatch,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Rate limit service unavailable."
            ),
        )

    async def should_not_resolve():
        raise AssertionError(
            "Organization resolution must not run "
            "when rate limit service is unavailable."
        )

    async def should_not_generate(
        **kwargs,
    ):
        raise AssertionError(
            "RAG generation must not run "
            "when rate limit service is unavailable."
        )

    monkeypatch.setattr(
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        should_not_resolve,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        should_not_generate,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "teste",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Rate limit service unavailable."
        )
    }


def test_public_rag_ignores_x_forwarded_for(
    monkeypatch,
):
    captured_keys = []

    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        captured_keys.append(
            kwargs["key"]
        )

        return RateLimitDecision(
            allowed=True,
            remaining=2,
            retry_after_seconds=0,
        )

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        return make_result()

    monkeypatch.setattr(
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    first = client.post(
        "/v1/rag/generate",
        headers={
            "X-Forwarded-For": (
                "198.51.100.10"
            ),
        },
        json={
            "question": "primeira",
        },
    )

    second = client.post(
        "/v1/rag/generate",
        headers={
            "X-Forwarded-For": (
                "203.0.113.99"
            ),
        },
        json={
            "question": "segunda",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert len(
        captured_keys
    ) == 2

    assert (
        captured_keys[0]
        == captured_keys[1]
    )
