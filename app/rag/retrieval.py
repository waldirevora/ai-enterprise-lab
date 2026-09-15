from dataclasses import dataclass
from typing import Any, Collection

import psycopg

from app.core.config import settings
from app.db.postgres import (
    DatabaseConnectionError,
    build_postgres_dsn,
)
from app.providers.ollama_embeddings import (
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderError,
)
from app.rag.text_processing import normalize_text


class RagRetrievalError(Exception):
    pass


@dataclass(frozen=True)
class RagSearchResult:
    chunk_id: int
    document_id: int
    title: str
    source: str
    source_uri: str | None
    classification: str
    chunk_index: int
    content: str
    metadata: dict[str, Any]
    similarity: float


embedding_provider = OllamaEmbeddingProvider(
    base_url=settings.ollama_base_url,
    expected_dimensions=settings.ai_embedding_dimensions,
)


def _vector_literal(
    embedding: list[float],
) -> str:
    if len(embedding) != settings.ai_embedding_dimensions:
        raise RagRetrievalError(
            "Query embedding dimensions do not match "
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


def _validate_classifications(
    classifications: Collection[str],
) -> list[str]:
    valid = {
        "public",
        "internal",
        "confidential",
    }

    values = list(dict.fromkeys(classifications))

    if not values:
        raise RagRetrievalError(
            "At least one allowed classification is required."
        )

    invalid = set(values) - valid

    if invalid:
        raise RagRetrievalError(
            "Invalid allowed classification."
        )

    return values


async def _search_database(
    *,
    embedding: list[float],
    allowed_classifications: list[str],
    limit: int,
) -> list[RagSearchResult]:
    vector = _vector_literal(embedding)

    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    c.id,
                    d.id,
                    d.title,
                    d.source,
                    d.source_uri,
                    d.classification,
                    c.chunk_index,
                    c.content,
                    c.metadata,
                    1 - (c.embedding <=> %s::vector)
                        AS similarity
                FROM rag_document_chunks c
                JOIN rag_documents d
                    ON d.id = c.document_id
                WHERE d.classification = ANY(%s::text[])
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s;
                """,
                (
                    vector,
                    allowed_classifications,
                    vector,
                    limit,
                ),
            )

            rows = await cursor.fetchall()

    return [
        RagSearchResult(
            chunk_id=row[0],
            document_id=row[1],
            title=row[2],
            source=row[3],
            source_uri=row[4],
            classification=row[5],
            chunk_index=row[6],
            content=row[7],
            metadata=row[8],
            similarity=float(row[9]),
        )
        for row in rows
    ]


async def retrieve_chunks(
    *,
    query: str,
    allowed_classifications: Collection[str],
    limit: int = 5,
) -> list[RagSearchResult]:
    normalized_query = normalize_text(query)

    if not normalized_query:
        raise RagRetrievalError(
            "Search query is empty."
        )

    if limit < 1 or limit > 20:
        raise RagRetrievalError(
            "Search limit must be between 1 and 20."
        )

    classifications = _validate_classifications(
        allowed_classifications
    )

    try:
        embedding = await embedding_provider.embed(
            model=settings.ai_embedding_model,
            text=normalized_query,
        )
    except OllamaEmbeddingProviderError as exc:
        raise RagRetrievalError(
            str(exc)
        ) from exc

    try:
        return await _search_database(
            embedding=embedding,
            allowed_classifications=classifications,
            limit=limit,
        )

    except (
        psycopg.Error,
        OSError,
        DatabaseConnectionError,
    ) as exc:
        raise RagRetrievalError(
            "Could not search the RAG database."
        ) from exc