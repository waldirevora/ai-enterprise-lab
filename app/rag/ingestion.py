from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.core.config import settings
from app.db.postgres import build_postgres_dsn
from app.providers.ollama_embeddings import (
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderError,
)
from app.rag.text_processing import (
    calculate_content_hash,
    chunk_text,
    normalize_text,
)


class RagIngestionError(Exception):
    pass


@dataclass(frozen=True)
class PreparedChunk:
    index: int
    content: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class IngestionResult:
    document_id: int
    content_hash: str
    chunks_inserted: int
    duplicate: bool


embedding_provider = OllamaEmbeddingProvider(
    base_url=settings.ollama_base_url,
    expected_dimensions=settings.ai_embedding_dimensions,
)


def _vector_literal(
    embedding: list[float],
) -> str:
    if len(embedding) != settings.ai_embedding_dimensions:
        raise RagIngestionError(
            "Embedding dimensions do not match "
            "the configured RAG dimensions."
        )

    return (
        "["
        + ",".join(
            repr(float(value))
            for value in embedding
        )
        + "]"
    )


async def _find_existing_document_id(
    *,
    source: str,
    content_hash: str,
) -> int | None:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT id
                FROM rag_documents
                WHERE source = %s
                  AND content_hash = %s;
                """,
                (
                    source,
                    content_hash,
                ),
            )

            row = await cursor.fetchone()

    if row is None:
        return None

    return row[0]


async def _persist_document(
    *,
    title: str,
    source: str,
    source_uri: str | None,
    classification: str,
    content_hash: str,
    metadata: dict[str, Any],
    prepared_chunks: list[PreparedChunk],
) -> tuple[int, bool]:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO rag_documents (
                    title,
                    source,
                    source_uri,
                    classification,
                    content_hash,
                    metadata
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (
                    source,
                    content_hash
                )
                DO NOTHING
                RETURNING id;
                """,
                (
                    title,
                    source,
                    source_uri,
                    classification,
                    content_hash,
                    Jsonb(metadata),
                ),
            )

            row = await cursor.fetchone()

            if row is None:
                await cursor.execute(
                    """
                    SELECT id
                    FROM rag_documents
                    WHERE source = %s
                      AND content_hash = %s;
                    """,
                    (
                        source,
                        content_hash,
                    ),
                )

                existing = await cursor.fetchone()

                if existing is None:
                    raise RagIngestionError(
                        "Could not resolve duplicate document."
                    )

                return existing[0], True

            document_id = row[0]

            for chunk in prepared_chunks:
                await cursor.execute(
                    """
                    INSERT INTO rag_document_chunks (
                        document_id,
                        chunk_index,
                        content,
                        embedding,
                        embedding_model,
                        metadata
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s::vector,
                        %s,
                        %s
                    );
                    """,
                    (
                        document_id,
                        chunk.index,
                        chunk.content,
                        _vector_literal(
                            chunk.embedding
                        ),
                        settings.ai_embedding_model,
                        Jsonb(chunk.metadata),
                    ),
                )

    return document_id, False


async def ingest_document(
    *,
    title: str,
    source: str,
    text: str,
    classification: str = "internal",
    source_uri: str | None = None,
    metadata: dict[str, Any] | None = None,
    chunk_size_words: int = 220,
    overlap_words: int = 40,
) -> IngestionResult:
    if classification not in {
        "public",
        "internal",
        "confidential",
    }:
        raise RagIngestionError(
            "Invalid document classification."
        )

    normalized = normalize_text(text)

    if not normalized:
        raise RagIngestionError(
            "Document text is empty."
        )

    content_hash = calculate_content_hash(
        normalized
    )

    try:
        existing_id = await _find_existing_document_id(
            source=source,
            content_hash=content_hash,
        )
    except psycopg.Error as exc:
        raise RagIngestionError(
            "Could not query PostgreSQL."
        ) from exc

    if existing_id is not None:
        return IngestionResult(
            document_id=existing_id,
            content_hash=content_hash,
            chunks_inserted=0,
            duplicate=True,
        )

    chunks = chunk_text(
        normalized,
        chunk_size_words=chunk_size_words,
        overlap_words=overlap_words,
    )

    prepared_chunks: list[PreparedChunk] = []

    try:
        for chunk in chunks:
            embedding = await embedding_provider.embed(
                model=settings.ai_embedding_model,
                text=chunk.content,
            )

            prepared_chunks.append(
                PreparedChunk(
                    index=chunk.index,
                    content=chunk.content,
                    embedding=embedding,
                    metadata={
                        "word_count": chunk.word_count,
                        "start_word": chunk.start_word,
                        "end_word": chunk.end_word,
                    },
                )
            )

    except OllamaEmbeddingProviderError as exc:
        raise RagIngestionError(
            str(exc)
        ) from exc

    try:
        document_id, duplicate = (
            await _persist_document(
                title=title,
                source=source,
                source_uri=source_uri,
                classification=classification,
                content_hash=content_hash,
                metadata=metadata or {},
                prepared_chunks=prepared_chunks,
            )
        )

    except psycopg.Error as exc:
        raise RagIngestionError(
            "Could not persist RAG document."
        ) from exc

    return IngestionResult(
        document_id=document_id,
        content_hash=content_hash,
        chunks_inserted=(
            0
            if duplicate
            else len(prepared_chunks)
        ),
        duplicate=duplicate,
    )