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


def make_grant() -> UnitAccessGrant:
    return UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification="internal",
    )


def test_generate_rag_answer_forwards_unit_grants(
    monkeypatch,
):
    grant = make_grant()

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

    #
    # Sem principal explícito, mantém
    # contrato histórico.
    #
    assert (
        "principal_id"
        not in captured
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


def test_generate_rag_answer_forwards_principal_without_unit_grants(
    monkeypatch,
):
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
                principal_id=77,
                question="Documento restrito",
                question_classification="internal",
                allowed_classifications={
                    "public",
                    "internal",
                },
            )
        )

    assert captured["organization_id"] == 42

    assert captured["principal_id"] == 77

    assert captured["query"] == (
        "Documento restrito"
    )

    assert (
        "unit_grants"
        not in captured
    )


def test_generate_rag_answer_forwards_principal_and_unit_grants(
    monkeypatch,
):
    grant = make_grant()

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
                principal_id=77,
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

    assert captured["principal_id"] == 77

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