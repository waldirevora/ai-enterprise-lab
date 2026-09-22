import asyncio

import pytest

from app.cli import revoke_api_key as module


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement, params=None):
        self.statements.append(" ".join(statement.split()))

    async def fetchone(self):
        if not self.rows:
            return None
        return self.rows.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor


def install_fake_database(monkeypatch, rows):
    cursor = FakeCursor(rows)
    connection = FakeConnection(cursor)

    async def fake_connect(*args, **kwargs):
        return connection

    monkeypatch.setattr(
        module.psycopg.AsyncConnection,
        "connect",
        fake_connect,
    )
    monkeypatch.setattr(
        module,
        "build_postgres_dsn",
        lambda: "fake-dsn",
    )
    monkeypatch.setattr(
        module,
        "extract_key_prefix",
        lambda token: "ael_test_prefix",
    )
    monkeypatch.setattr(
        module,
        "hash_api_key",
        lambda token: "0" * 64,
    )
    return cursor


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.delenv("AEL_API_KEY", raising=False)
    with pytest.raises(
        module.RevokeApiKeyError,
        match="AEL_API_KEY is not configured",
    ):
        module._read_api_key()


def test_active_credential_is_revoked(monkeypatch):
    cursor = install_fake_database(
        monkeypatch,
        [(42, "ael_test_prefix")],
    )
    result = asyncio.run(module.revoke_api_key("test-token"))
    assert result.credential_id == 42
    assert result.already_revoked is False
    assert "UPDATE api_credentials" in cursor.statements[0]


def test_already_revoked_is_idempotent(monkeypatch):
    install_fake_database(
        monkeypatch,
        [None, (42, "ael_test_prefix", object())],
    )
    result = asyncio.run(module.revoke_api_key("test-token"))
    assert result.credential_id == 42
    assert result.already_revoked is True


def test_unknown_credential_is_rejected(monkeypatch):
    install_fake_database(monkeypatch, [None, None])
    with pytest.raises(
        module.RevokeApiKeyError,
        match="was not found",
    ):
        asyncio.run(module.revoke_api_key("test-token"))


def test_invalid_format_is_rejected():
    with pytest.raises(
        module.RevokeApiKeyError,
        match="Invalid API key format",
    ):
        asyncio.run(module.revoke_api_key("invalid"))
