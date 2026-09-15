import asyncio

import pytest

from app.rag import retrieval
from app.rag.retrieval import (
    RagRetrievalError,
    RagSearchResult,
    retrieve_chunks,
)


def test_empty_query_is_rejected():
    with pytest.raises(
        RagRetrievalError,
        match="Search query is empty",
    ):
        asyncio.run(
            retrieve_chunks(
                query="   ",
                allowed_classifications={"public"},
            )
        )


def test_empty_classifications_are_rejected():
    with pytest.raises(
        RagRetrievalError,
        match="At least one allowed classification",
    ):
        asyncio.run(
            retrieve_chunks(
                query="teste",
                allowed_classifications=set(),
            )
        )


def test_invalid_classification_is_rejected():
    with pytest.raises(
        RagRetrievalError,
        match="Invalid allowed classification",
    ):
        asyncio.run(
            retrieve_chunks(
                query="teste",
                allowed_classifications={"secret"},
            )
        )


def test_invalid_limit_is_rejected():
    with pytest.raises(
        RagRetrievalError,
        match="Search limit must be between",
    ):
        asyncio.run(
            retrieve_chunks(
                query="teste",
                allowed_classifications={"public"},
                limit=21,
            )
        )


def test_successful_retrieval(
    monkeypatch,
):
    captured = {}

    async def fake_embed(
        *,
        model,
        text,
    ):
        captured["model"] = model
        captured["text"] = text

        return [0.1] * 1024

    async def fake_search_database(
        *,
        embedding,
        allowed_classifications,
        limit,
    ):
        captured["dimensions"] = len(embedding)
        captured["classifications"] = (
            allowed_classifications
        )
        captured["limit"] = limit

        return [
            RagSearchResult(
                chunk_id=10,
                document_id=5,
                title="Documento",
                source="test",
                source_uri=None,
                classification="internal",
                chunk_index=0,
                content="Conteudo relevante",
                metadata={},
                similarity=0.91,
            )
        ]

    monkeypatch.setattr(
        retrieval.embedding_provider,
        "embed",
        fake_embed,
    )

    monkeypatch.setattr(
        retrieval,
        "_search_database",
        fake_search_database,
    )

    result = asyncio.run(
        retrieve_chunks(
            query="  pergunta   empresarial ",
            allowed_classifications={
                "public",
                "internal",
            },
            limit=3,
        )
    )

    assert len(result) == 1
    assert result[0].similarity == 0.91
    assert result[0].classification == "internal"

    assert captured["text"] == (
        "pergunta empresarial"
    )

    assert captured["dimensions"] == 1024
    assert captured["limit"] == 3
    assert set(
        captured["classifications"]
    ) == {
        "public",
        "internal",
    }