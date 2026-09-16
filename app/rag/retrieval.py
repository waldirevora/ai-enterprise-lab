from dataclasses import dataclass
from typing import Any, Iterable

import psycopg

from app.access.unit_grants import UnitAccessGrant
from app.core.config import settings
from app.db.postgres import build_postgres_dsn
from app.providers.ollama_embeddings import (
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderError,
)


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


_VALID_CLASSIFICATIONS = {
    "public",
    "internal",
    "confidential",
}


def _vector_literal(
    embedding: list[float],
) -> str:
    if (
        len(embedding)
        != settings.ai_embedding_dimensions
    ):
        raise RagRetrievalError(
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


def _validate_classifications(
    classifications: Iterable[str],
) -> frozenset[str]:
    values = frozenset(
        classifications
    )

    if not values:
        raise RagRetrievalError(
            "At least one allowed classification "
            "must be provided."
        )

    if not values.issubset(
        _VALID_CLASSIFICATIONS
    ):
        raise RagRetrievalError(
            "Invalid allowed classification."
        )

    return values


def _normalize_unit_grants(
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ],
) -> tuple[
    tuple[int, frozenset[str]],
    ...,
]:
    normalized: dict[
        int,
        frozenset[str],
    ] = {}

    for grant in unit_grants:
        unit_id = (
            grant.organizational_unit_id
        )

        if unit_id < 1:
            raise RagRetrievalError(
                "organizational_unit_id must be "
                "a positive integer."
            )

        allowed = _validate_classifications(
            grant.allowed_classifications
        )

        existing = normalized.get(
            unit_id
        )

        if existing is None:
            normalized[unit_id] = allowed

        else:
            # Defense in depth:
            # duplicate grants for the same unit
            # can only reduce permissions.
            normalized[unit_id] = (
                existing.intersection(
                    allowed
                )
            )

    return tuple(
        (
            unit_id,
            allowed,
        )
        for unit_id, allowed
        in sorted(
            normalized.items()
        )
        if allowed
    )


def _build_scope_filter(
    *,
    corporate_allowed_classifications: (
        frozenset[str]
    ),
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ],
) -> tuple[
    str,
    list[Any],
]:
    clauses = [
        """
        (
            d.organizational_unit_id IS NULL
            AND d.classification
                = ANY(%s::text[])
        )
        """
    ]

    params: list[Any] = [
        sorted(
            corporate_allowed_classifications
        )
    ]

    normalized_grants = (
        _normalize_unit_grants(
            unit_grants
        )
    )

    for (
        organizational_unit_id,
        allowed_classifications,
    ) in normalized_grants:
        clauses.append(
            """
            (
                d.organizational_unit_id = %s
                AND d.classification
                    = ANY(%s::text[])
            )
            """
        )

        params.extend(
            [
                organizational_unit_id,
                sorted(
                    allowed_classifications
                ),
            ]
        )

    return (
        "("
        + " OR ".join(clauses)
        + ")",
        params,
    )


def _build_acl_filter(
    *,
    principal_id: int | None,
) -> tuple[
    str,
    list[Any],
]:
    #
    # Sem principal autenticado:
    #
    # documentos restricted nunca podem
    # entrar no conjunto candidato.
    #
    if principal_id is None:
        return (
            "d.access_mode = 'inherited'",
            [],
        )

    if principal_id < 1:
        raise RagRetrievalError(
            "principal_id must be a positive integer."
        )

    #
    # Com principal autenticado:
    #
    # inherited continua seguindo as camadas
    # superiores normalmente.
    #
    # restricted exige ACL read ativa.
    #
    return (
        """
        (
            d.access_mode = 'inherited'
            OR (
                d.access_mode = 'restricted'
                AND EXISTS (
                    SELECT 1
                    FROM rag_document_acl_entries a
                    WHERE a.organization_id
                        = d.organization_id
                      AND a.document_id
                        = d.id
                      AND a.principal_id
                        = %s
                      AND a.permission
                        = 'read'
                      AND a.status
                        = 'active'
                )
            )
        )
        """,
        [
            principal_id,
        ],
    )


async def _search_database(
    *,
    organization_id: int,
    embedding: list[float],
    allowed_classifications: (
        frozenset[str]
        | set[str]
    ),
    limit: int,
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ] = (),
    principal_id: int | None = None,
) -> list[RagSearchResult]:
    corporate_allowed = (
        _validate_classifications(
            allowed_classifications
        )
    )

    scope_sql, scope_params = (
        _build_scope_filter(
            corporate_allowed_classifications=(
                corporate_allowed
            ),
            unit_grants=unit_grants,
        )
    )

    acl_sql, acl_params = (
        _build_acl_filter(
            principal_id=principal_id,
        )
    )

    vector = _vector_literal(
        embedding
    )

    sql = f"""
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
            1 - (
                c.embedding <=> %s::vector
            ) AS similarity

        FROM rag_document_chunks c

        JOIN rag_documents d
            ON d.id = c.document_id

        WHERE d.organization_id = %s
          AND {scope_sql}
          AND {acl_sql}

        ORDER BY similarity DESC

        LIMIT %s;
    """

    params: list[Any] = [
        vector,
        organization_id,
        *scope_params,
        *acl_params,
        limit,
    ]

    try:
        async with await psycopg.AsyncConnection.connect(
            build_postgres_dsn(),
            connect_timeout=5,
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    sql,
                    params,
                )

                rows = await cursor.fetchall()

    except psycopg.Error as exc:
        raise RagRetrievalError(
            "Could not query RAG documents."
        ) from exc

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
    organization_id: int,
    query: str,
    allowed_classifications: (
        set[str]
        | frozenset[str]
    ),
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ] = (),
    principal_id: int | None = None,
    limit: int = 5,
) -> list[RagSearchResult]:
    if organization_id < 1:
        raise RagRetrievalError(
            "organization_id must be a positive integer."
        )

    if (
        principal_id is not None
        and principal_id < 1
    ):
        raise RagRetrievalError(
            "principal_id must be a positive integer."
        )

    normalized_query = " ".join(
        query.split()
    )

    if not normalized_query:
        raise RagRetrievalError(
            "Search query is empty."
        )

    normalized_classifications = (
        _validate_classifications(
            allowed_classifications
        )
    )

    if limit < 1 or limit > 20:
        raise RagRetrievalError(
            "Search limit must be between "
            "1 and 20."
        )

    try:
        embedding = (
            await embedding_provider.embed(
                model=(
                    settings.ai_embedding_model
                ),
                text=normalized_query,
            )
        )

    except OllamaEmbeddingProviderError as exc:
        raise RagRetrievalError(
            str(exc)
        ) from exc

    #
    # Preserve legacy internal call shapes
    # whenever optional authorization data
    # is absent.
    #
    # Isso mantém compatibilidade com mocks
    # e callers anteriores.
    #
    if (
        not unit_grants
        and principal_id is None
    ):
        return await _search_database(
            organization_id=organization_id,
            embedding=embedding,
            allowed_classifications=(
                normalized_classifications
            ),
            limit=limit,
        )

    if principal_id is None:
        return await _search_database(
            organization_id=organization_id,
            embedding=embedding,
            allowed_classifications=(
                normalized_classifications
            ),
            unit_grants=unit_grants,
            limit=limit,
        )

    if not unit_grants:
        return await _search_database(
            organization_id=organization_id,
            embedding=embedding,
            allowed_classifications=(
                normalized_classifications
            ),
            principal_id=principal_id,
            limit=limit,
        )

    return await _search_database(
        organization_id=organization_id,
        embedding=embedding,
        allowed_classifications=(
            normalized_classifications
        ),
        unit_grants=unit_grants,
        principal_id=principal_id,
        limit=limit,
    )