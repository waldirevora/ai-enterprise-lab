import asyncio

import pytest

from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.agents import tools
from app.agents.tools import (
    AgentToolError,
    search_enterprise_knowledge,
)
from app.rag.retrieval import (
    RagRetrievalError,
    RagSearchResult,
)


def make_result(
    *,
    document_id: int,
    classification: str = "internal",
    content: str = "conteudo autorizado",
) -> RagSearchResult:
    return RagSearchResult(
        chunk_id=document_id * 10,
        document_id=document_id,
        title=f"Documento {document_id}",
        source="agent-test",
        source_uri=None,
        classification=classification,
        chunk_index=0,
        content=content,
        metadata={},
        similarity=0.95,
    )


def test_search_forwards_server_side_authority(
    monkeypatch,
):
    captured = {}

    grant = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification=(
            "internal"
        ),
    )

    async def fake_retrieve_chunks(
        **kwargs,
    ):
        captured.update(kwargs)

        return [
            make_result(
                document_id=1
            )
        ]

    monkeypatch.setattr(
        tools,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    result = asyncio.run(
        search_enterprise_knowledge(
            organization_id=42,
            principal_id=10,
            query="Qual é a política?",
            allowed_classifications={
                "public",
                "internal",
            },
            unit_grants=(
                grant,
            ),
            retrieval_limit=4,
            max_context_chunks=3,
            max_context_characters=2000,
        )
    )

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
            "allowed_classifications"
        ]
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )

    assert captured["unit_grants"] == (
        grant,
    )

    assert captured["limit"] == 4

    assert (
        result.context.chunks_used
        == 1
    )


@pytest.mark.parametrize(
    "organization_id,principal_id",
    [
        (0, 10),
        (42, 0),
    ],
)
def test_search_rejects_invalid_authority(
    organization_id,
    principal_id,
):
    with pytest.raises(
        AgentToolError,
        match="Invalid agent authority",
    ):
        asyncio.run(
            search_enterprise_knowledge(
                organization_id=(
                    organization_id
                ),
                principal_id=(
                    principal_id
                ),
                query="teste",
                allowed_classifications={
                    "public"
                },
            )
        )


def test_search_returns_only_chunks_used_by_context(
    monkeypatch,
):
    async def fake_retrieve_chunks(
        **kwargs,
    ):
        return [
            make_result(
                document_id=1,
                content="primeiro",
            ),
            make_result(
                document_id=2,
                content="segundo",
            ),
            make_result(
                document_id=3,
                content="terceiro",
            ),
        ]

    monkeypatch.setattr(
        tools,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    result = asyncio.run(
        search_enterprise_knowledge(
            organization_id=42,
            principal_id=10,
            query="teste",
            allowed_classifications={
                "internal"
            },
            max_context_chunks=2,
        )
    )

    assert (
        result.context.chunks_used
        == 2
    )

    assert len(
        result.retrieved_chunks
    ) == 2

    assert (
        result.retrieved_chunks[0]
        .document_id
        == 1
    )

    assert (
        result.retrieved_chunks[1]
        .document_id
        == 2
    )


def test_search_allows_empty_authorized_result(
    monkeypatch,
):
    async def fake_retrieve_chunks(
        **kwargs,
    ):
        return []

    monkeypatch.setattr(
        tools,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    result = asyncio.run(
        search_enterprise_knowledge(
            organization_id=42,
            principal_id=10,
            query="teste",
            allowed_classifications={
                "internal"
            },
        )
    )

    assert (
        result.retrieved_chunks
        == ()
    )

    assert result.context.text == ""

    assert (
        result.context.chunks_used
        == 0
    )

    assert (
        result.context
        .effective_classification
        is None
    )


def test_retrieval_failure_is_sanitized(
    monkeypatch,
):
    async def fake_retrieve_chunks(
        **kwargs,
    ):
        raise RagRetrievalError(
            "PRIVATE_DATABASE_DETAIL"
        )

    monkeypatch.setattr(
        tools,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    with pytest.raises(
        AgentToolError,
        match=(
            "Enterprise knowledge "
            "search unavailable"
        ),
    ) as exc_info:
        asyncio.run(
            search_enterprise_knowledge(
                organization_id=42,
                principal_id=10,
                query="teste",
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert (
        "PRIVATE_DATABASE_DETAIL"
        not in str(
            exc_info.value
        )
    )
