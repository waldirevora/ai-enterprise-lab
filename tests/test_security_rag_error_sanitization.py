import pytest
from fastapi.testclient import TestClient

from app.api import rag as rag_api
from app.main import app
from app.rag.service import RagServiceError


client = TestClient(app)


@pytest.mark.parametrize(
    "internal_detail",
    [
        "Authorized RAG context is empty.",
        (
            "RAG context classification "
            "could not be determined."
        ),
    ],
)
def test_public_rag_internal_error_is_not_exposed(
    monkeypatch,
    internal_detail,
):
    async def fake_enforce_rate_limit(
        **kwargs,
    ):
        return None

    async def fake_resolve_organization():
        return 42

    async def fake_generate_rag_answer(
        **kwargs,
    ):
        raise RagServiceError(
            internal_detail
        )

    monkeypatch.setattr(
        rag_api,
        "enforce_rate_limit",
        fake_enforce_rate_limit,
    )

    monkeypatch.setattr(
        rag_api,
        "_resolve_public_organization_id",
        fake_resolve_organization,
    )

    monkeypatch.setattr(
        rag_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        "/v1/rag/generate",
        json={
            "question": "test",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "RAG service unavailable."
    }

    assert (
        internal_detail
        not in response.text
    )
