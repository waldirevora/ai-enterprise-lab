import asyncio

import pytest

from app.rag import ingestion
from app.rag.ingestion import (
    RagIngestionError,
    ingest_document,
)


def test_empty_document_is_rejected():
    with pytest.raises(
        RagIngestionError,
        match="Document text is empty",
    ):
        asyncio.run(
            ingest_document(
                organization_id=1,
                title="Teste",
                source="test",
                text="   ",
            )
        )


def test_invalid_classification_is_rejected():
    with pytest.raises(
        RagIngestionError,
        match="Invalid document classification",
    ):
        asyncio.run(
            ingest_document(
                organization_id=1,
                title="Teste",
                source="test",
                text="conteudo",
                classification="secret",
            )
        )


def test_duplicate_document_skips_embeddings(
    monkeypatch,
):
    async def fake_find_existing_document_id(
        *,
        organization_id,
        source,
        content_hash,
    ):
        return 123

    async def should_not_embed(
        *,
        model,
        text,
    ):
        raise AssertionError(
            "Embedding should not be generated."
        )

    monkeypatch.setattr(
        ingestion,
        "_find_existing_document_id",
        fake_find_existing_document_id,
    )

    monkeypatch.setattr(
        ingestion.embedding_provider,
        "embed",
        should_not_embed,
    )

    result = asyncio.run(
        ingest_document(
            organization_id=1,
            title="Documento",
            source="test",
            text="conteudo duplicado",
        )
    )

    assert result.document_id == 123
    assert result.duplicate is True
    assert result.chunks_inserted == 0


def test_successful_ingestion(
    monkeypatch,
):
    captured = {}

    async def fake_find_existing_document_id(
        *,
        organization_id,
        source,
        content_hash,
    ):
        return None

    async def fake_embed(
        *,
        model,
        text,
    ):
        return [0.1] * 1024

    async def fake_persist_document(
        **kwargs,
    ):
        captured.update(kwargs)

        return 456, False

    monkeypatch.setattr(
        ingestion,
        "_find_existing_document_id",
        fake_find_existing_document_id,
    )

    monkeypatch.setattr(
        ingestion.embedding_provider,
        "embed",
        fake_embed,
    )

    monkeypatch.setattr(
        ingestion,
        "_persist_document",
        fake_persist_document,
    )

    text = " ".join(
        f"word{i}"
        for i in range(10)
    )

    result = asyncio.run(
        ingest_document(
            organization_id=1,
            title="Documento",
            source="test",
            text=text,
            classification="internal",
            chunk_size_words=4,
            overlap_words=1,
        )
    )

    assert result.document_id == 456
    assert result.duplicate is False
    assert result.chunks_inserted == 3

    assert captured["organization_id"] == 1

    prepared_chunks = captured[
        "prepared_chunks"
    ]

    assert len(prepared_chunks) == 3

    assert len(
        prepared_chunks[0].embedding
    ) == 1024


def test_vector_dimension_is_validated():
    with pytest.raises(
        RagIngestionError,
        match="Embedding dimensions",
    ):
        ingestion._vector_literal(
            [0.1] * 768
        )


def test_invalid_organization_id_is_rejected():
    with pytest.raises(
        RagIngestionError,
        match="organization_id must be a positive integer",
    ):
        asyncio.run(
            ingest_document(
                organization_id=0,
                title="Teste",
                source="test",
                text="conteudo",
            )
        )


def test_duplicate_lookup_is_scoped_to_organization(
    monkeypatch,
):
    captured = {}

    async def fake_find_existing_document_id(
        *,
        organization_id,
        source,
        content_hash,
    ):
        captured["organization_id"] = (
            organization_id
        )

        return 321

    async def should_not_embed(
        *,
        model,
        text,
    ):
        raise AssertionError(
            "Embedding should not be generated."
        )

    monkeypatch.setattr(
        ingestion,
        "_find_existing_document_id",
        fake_find_existing_document_id,
    )

    monkeypatch.setattr(
        ingestion.embedding_provider,
        "embed",
        should_not_embed,
    )

    result = asyncio.run(
        ingest_document(
            organization_id=77,
            title="Documento",
            source="test",
            text="conteudo duplicado",
        )
    )

    assert captured["organization_id"] == 77
    assert result.document_id == 321
    assert result.duplicate is True
    assert result.chunks_inserted == 0