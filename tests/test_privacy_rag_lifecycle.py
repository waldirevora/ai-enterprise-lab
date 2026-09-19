import asyncio
from datetime import datetime, timezone

import psycopg
import pytest

from app.rag import lifecycle
from app.rag.lifecycle import (
    RagDocumentNotFoundError,
    RagLifecycleError,
)


class FakeCursor:
    def __init__(
        self,
        script,
    ):
        self.script = list(script)
        self.current = None
        self.executions = []

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def execute(
        self,
        query,
        params,
    ):
        self.executions.append(
            (
                query,
                params,
            )
        )

        if not self.script:
            raise AssertionError(
                "Unexpected SQL execution."
            )

        self.current = self.script.pop(0)

    async def fetchone(self):
        return self.current.get(
            "fetchone"
        )

    async def fetchall(self):
        return self.current.get(
            "fetchall",
            [],
        )


class FakeConnection:
    def __init__(
        self,
        cursor,
    ):
        self._cursor = cursor

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    def cursor(self):
        return self._cursor


def install_connection(
    monkeypatch,
    *,
    script,
):
    cursor = FakeCursor(
        script
    )

    connection = FakeConnection(
        cursor
    )

    async def fake_connect():
        return connection

    monkeypatch.setattr(
        lifecycle,
        "_connect",
        fake_connect,
    )

    return cursor


@pytest.mark.parametrize(
    (
        "organization_id",
        "document_id",
    ),
    [
        (0, 1),
        (1, 0),
    ],
)
def test_export_requires_positive_ids(
    organization_id,
    document_id,
):
    with pytest.raises(
        RagLifecycleError,
    ):
        asyncio.run(
            lifecycle.export_rag_document(
                organization_id=organization_id,
                document_id=document_id,
            )
        )


@pytest.mark.parametrize(
    (
        "organization_id",
        "document_id",
    ),
    [
        (0, 1),
        (1, 0),
    ],
)
def test_delete_requires_positive_ids(
    organization_id,
    document_id,
):
    with pytest.raises(
        RagLifecycleError,
    ):
        asyncio.run(
            lifecycle.delete_rag_document(
                organization_id=organization_id,
                document_id=document_id,
            )
        )


def test_export_is_organization_scoped(
    monkeypatch,
):
    now = datetime.now(
        timezone.utc
    )

    cursor = install_connection(
        monkeypatch,
        script=[
            {
                "fetchone": (
                    10,
                    42,
                    5,
                    7,
                    "Documento",
                    "manual",
                    "https://internal/doc",
                    "internal",
                    "restricted",
                    "abc123",
                    {
                        "department": "finance",
                    },
                    now,
                    now,
                ),
            },
            {
                "fetchall": [
                    (
                        100,
                        0,
                        "PRIVATE_CONTENT",
                        3,
                        "embedding-model",
                        {
                            "word_count": 3,
                        },
                        now,
                    ),
                ],
            },
            {
                "fetchall": [
                    (
                        500,
                        99,
                        "read",
                        "active",
                        7,
                        now,
                        now,
                    ),
                ],
            },
        ],
    )

    result = asyncio.run(
        lifecycle.export_rag_document(
            organization_id=42,
            document_id=10,
        )
    )

    assert result.document_id == 10
    assert result.organization_id == 42
    assert result.title == "Documento"

    assert (
        result.chunks[0].content
        == "PRIVATE_CONTENT"
    )

    assert (
        result.acl_entries[0].principal_id
        == 99
    )

    assert len(
        cursor.executions
    ) == 3

    for _, params in cursor.executions:
        assert params == (
            10,
            42,
        )

    combined_sql = " ".join(
        query
        for query, _ in cursor.executions
    )

    assert "c.embedding," not in combined_sql


def test_export_missing_or_cross_tenant_is_not_found(
    monkeypatch,
):
    cursor = install_connection(
        monkeypatch,
        script=[
            {
                "fetchone": None,
            },
        ],
    )

    with pytest.raises(
        RagDocumentNotFoundError,
        match="RAG document was not found",
    ):
        asyncio.run(
            lifecycle.export_rag_document(
                organization_id=42,
                document_id=10,
            )
        )

    assert len(
        cursor.executions
    ) == 1

    _, params = cursor.executions[0]

    assert params == (
        10,
        42,
    )


def test_delete_is_organization_scoped(
    monkeypatch,
):
    cursor = install_connection(
        monkeypatch,
        script=[
            {
                "fetchone": (
                    10,
                ),
            },
        ],
    )

    deleted_id = asyncio.run(
        lifecycle.delete_rag_document(
            organization_id=42,
            document_id=10,
        )
    )

    assert deleted_id == 10

    assert len(
        cursor.executions
    ) == 1

    query, params = (
        cursor.executions[0]
    )

    assert (
        "DELETE FROM rag_documents"
        in query
    )

    assert (
        "organization_id = %s"
        in query
    )

    assert params == (
        10,
        42,
    )


def test_delete_missing_or_cross_tenant_is_not_found(
    monkeypatch,
):
    install_connection(
        monkeypatch,
        script=[
            {
                "fetchone": None,
            },
        ],
    )

    with pytest.raises(
        RagDocumentNotFoundError,
        match="RAG document was not found",
    ):
        asyncio.run(
            lifecycle.delete_rag_document(
                organization_id=42,
                document_id=999,
            )
        )


@pytest.mark.parametrize(
    "operation",
    [
        "export",
        "delete",
    ],
)
def test_database_failure_is_sanitized(
    monkeypatch,
    operation,
):
    async def fail_connect():
        raise psycopg.OperationalError(
            "PRIVATE_DATABASE_DETAIL"
        )

    monkeypatch.setattr(
        lifecycle,
        "_connect",
        fail_connect,
    )

    if operation == "export":
        coroutine = (
            lifecycle.export_rag_document(
                organization_id=1,
                document_id=1,
            )
        )

    else:
        coroutine = (
            lifecycle.delete_rag_document(
                organization_id=1,
                document_id=1,
            )
        )

    with pytest.raises(
        RagLifecycleError,
        match=(
            "RAG lifecycle service unavailable"
        ),
    ) as exc_info:
        asyncio.run(
            coroutine
        )

    assert (
        "PRIVATE_DATABASE_DETAIL"
        not in str(exc_info.value)
    )
