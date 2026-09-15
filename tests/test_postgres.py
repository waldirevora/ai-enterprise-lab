import pytest

from app.core.config import settings
from app.db.postgres import (
    DatabaseConnectionError,
    build_postgres_dsn,
)


def test_build_postgres_dsn(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "postgres_host",
        "127.0.0.1",
    )
    monkeypatch.setattr(
        settings,
        "postgres_port",
        5432,
    )
    monkeypatch.setattr(
        settings,
        "postgres_db",
        "ai_enterprise_lab",
    )
    monkeypatch.setattr(
        settings,
        "postgres_user",
        "ai_lab",
    )
    monkeypatch.setattr(
        settings,
        "postgres_password",
        "test-password",
    )

    dsn = build_postgres_dsn()

    assert "host=127.0.0.1" in dsn
    assert "port=5432" in dsn
    assert "dbname=ai_enterprise_lab" in dsn
    assert "user=ai_lab" in dsn
    assert "password=test-password" in dsn


def test_missing_password_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "postgres_password",
        "",
    )

    with pytest.raises(
        DatabaseConnectionError,
        match="password is not configured",
    ):
        build_postgres_dsn()