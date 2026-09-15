import asyncio

import pytest

from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.rag import service
from app.rag.service import (
    RagServiceError,
    generate_rag_answer,
)


def test_generate_rag_answer_forwards_unit_grants(
    monkeypatch,
):
    grant = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification="internal",
    )

    captured = {}

    async def fake_retrieve_chunks(
        **kwargs,
    ):
        captured.update(kwargs)

        return []

    monkeypatch.setattr(
        service,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    with pytest.raises(
        RagServiceError,
        match="No authorized RAG context was found",
    ):
        asyncio.run(
            generate_rag_answer(
                organization_id=42,
                question="Pergunta Financeiro",
                question_classification="internal",
                allowed_classifications={
                    "public",
                    "internal",
                },
                unit_grants=(
                    grant,
                ),
            )
        )

    assert captured["organization_id"] == 42

    assert captured["unit_grants"] == (
        grant,
    )

    assert (
        captured["allowed_classifications"]
        == {
            "public",
            "internal",
        }
    )


def test_generate_rag_answer_without_grants_preserves_legacy_call(
    monkeypatch,
):
    captured = {}

    async def fake_retrieve_chunks(
        *,
        organization_id,
        query,
        allowed_classifications,
        limit,
    ):
        captured["organization_id"] = (
            organization_id
        )
        captured["query"] = query
        captured["allowed_classifications"] = (
            allowed_classifications
        )
        captured["limit"] = limit

        return []

    monkeypatch.setattr(
        service,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    with pytest.raises(
        RagServiceError,
        match="No authorized RAG context was found",
    ):
        asyncio.run(
            generate_rag_answer(
                organization_id=42,
                question="Pergunta corporate",
                question_classification="internal",
                allowed_classifications={
                    "public",
                    "internal",
                },
            )
        )

    assert captured == {
        "organization_id": 42,
        "query": "Pergunta corporate",
        "allowed_classifications": {
            "public",
            "internal",
        },
        "limit": 5,
    }