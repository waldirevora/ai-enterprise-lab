from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg

from app.db.postgres import (
    DatabaseConnectionError,
    build_postgres_dsn,
)


class RagLifecycleError(Exception):
    pass


class RagDocumentNotFoundError(
    RagLifecycleError
):
    pass


@dataclass(frozen=True)
class RagDocumentChunkExport:
    chunk_id: int
    chunk_index: int
    content: str
    token_count: int | None
    embedding_model: str
    metadata: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class RagDocumentAclExport:
    acl_entry_id: int
    principal_id: int
    permission: str
    status: str
    created_by_principal_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RagDocumentExport:
    document_id: int
    organization_id: int
    organizational_unit_id: int | None
    created_by_principal_id: int | None

    title: str
    source: str
    source_uri: str | None

    classification: str
    access_mode: str

    content_hash: str
    metadata: dict[str, Any]

    created_at: datetime
    updated_at: datetime

    chunks: tuple[
        RagDocumentChunkExport,
        ...,
    ]

    acl_entries: tuple[
        RagDocumentAclExport,
        ...,
    ]


def _validate_identity(
    *,
    organization_id: int,
    document_id: int,
) -> None:
    if organization_id < 1:
        raise RagLifecycleError(
            "organization_id must be "
            "a positive integer."
        )

    if document_id < 1:
        raise RagLifecycleError(
            "document_id must be "
            "a positive integer."
        )


async def _connect():
    return await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    )


async def export_rag_document(
    *,
    organization_id: int,
    document_id: int,
) -> RagDocumentExport:
    _validate_identity(
        organization_id=organization_id,
        document_id=document_id,
    )

    try:
        async with await _connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT
                        id,
                        organization_id,
                        organizational_unit_id,
                        created_by_principal_id,
                        title,
                        source,
                        source_uri,
                        classification,
                        access_mode,
                        content_hash,
                        metadata,
                        created_at,
                        updated_at
                    FROM rag_documents
                    WHERE id = %s
                      AND organization_id = %s;
                    """,
                    (
                        document_id,
                        organization_id,
                    ),
                )

                document_row = (
                    await cursor.fetchone()
                )

                if document_row is None:
                    raise RagDocumentNotFoundError(
                        "RAG document was not found."
                    )

                await cursor.execute(
                    """
                    SELECT
                        c.id,
                        c.chunk_index,
                        c.content,
                        c.token_count,
                        c.embedding_model,
                        c.metadata,
                        c.created_at
                    FROM rag_document_chunks c
                    JOIN rag_documents d
                      ON d.id = c.document_id
                    WHERE c.document_id = %s
                      AND d.organization_id = %s
                    ORDER BY
                        c.chunk_index,
                        c.id;
                    """,
                    (
                        document_id,
                        organization_id,
                    ),
                )

                chunk_rows = (
                    await cursor.fetchall()
                )

                await cursor.execute(
                    """
                    SELECT
                        a.id,
                        a.principal_id,
                        a.permission,
                        a.status,
                        a.created_by_principal_id,
                        a.created_at,
                        a.updated_at
                    FROM rag_document_acl_entries a
                    JOIN rag_documents d
                      ON d.id = a.document_id
                     AND d.organization_id
                         = a.organization_id
                    WHERE a.document_id = %s
                      AND a.organization_id = %s
                    ORDER BY a.id;
                    """,
                    (
                        document_id,
                        organization_id,
                    ),
                )

                acl_rows = (
                    await cursor.fetchall()
                )

    except RagDocumentNotFoundError:
        raise

    except (
        psycopg.Error,
        DatabaseConnectionError,
    ) as exc:
        raise RagLifecycleError(
            "RAG lifecycle service unavailable."
        ) from exc

    chunks = tuple(
        RagDocumentChunkExport(
            chunk_id=row[0],
            chunk_index=row[1],
            content=row[2],
            token_count=row[3],
            embedding_model=row[4],
            metadata=row[5],
            created_at=row[6],
        )
        for row in chunk_rows
    )

    acl_entries = tuple(
        RagDocumentAclExport(
            acl_entry_id=row[0],
            principal_id=row[1],
            permission=row[2],
            status=row[3],
            created_by_principal_id=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
        for row in acl_rows
    )

    return RagDocumentExport(
        document_id=document_row[0],
        organization_id=document_row[1],
        organizational_unit_id=(
            document_row[2]
        ),
        created_by_principal_id=(
            document_row[3]
        ),
        title=document_row[4],
        source=document_row[5],
        source_uri=document_row[6],
        classification=document_row[7],
        access_mode=document_row[8],
        content_hash=document_row[9],
        metadata=document_row[10],
        created_at=document_row[11],
        updated_at=document_row[12],
        chunks=chunks,
        acl_entries=acl_entries,
    )


async def delete_rag_document(
    *,
    organization_id: int,
    document_id: int,
) -> int:
    _validate_identity(
        organization_id=organization_id,
        document_id=document_id,
    )

    try:
        async with await _connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    DELETE FROM rag_documents
                    WHERE id = %s
                      AND organization_id = %s
                    RETURNING id;
                    """,
                    (
                        document_id,
                        organization_id,
                    ),
                )

                row = await cursor.fetchone()

                if row is None:
                    raise RagDocumentNotFoundError(
                        "RAG document was not found."
                    )

    except RagDocumentNotFoundError:
        raise

    except (
        psycopg.Error,
        DatabaseConnectionError,
    ) as exc:
        raise RagLifecycleError(
            "RAG lifecycle service unavailable."
        ) from exc

    return row[0]
