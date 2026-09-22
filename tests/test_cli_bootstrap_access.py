import asyncio
from types import SimpleNamespace

import pytest

from app.cli import bootstrap_access as module


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []
        self.params = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement, params=None):
        self.statements.append(
            " ".join(statement.split())
        )
        self.params.append(params)

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
        "generate_api_key",
        lambda: SimpleNamespace(
            token="ael_test_token",
            key_prefix="ael_test_prefix",
            secret_hash="0" * 64,
        ),
    )

    return cursor


def run_bootstrap(*, role="owner"):
    return asyncio.run(
        module.bootstrap_access(
            organization_slug="lab-default",
            organization_name="AI Enterprise Lab",
            display_name="Quickstart Owner",
            subject="quickstart-owner",
            role=role,
            max_classification="internal",
            credential_name="quickstart",
        )
    )


def test_bootstrap_creates_missing_access_records(monkeypatch):
    cursor = install_fake_database(
        monkeypatch,
        [
            None,
            (10,),
            None,
            (20,),
            None,
        ],
    )

    result = run_bootstrap()
    sql = "\\n".join(cursor.statements)

    assert result.organization_id == 10
    assert result.principal_id == 20
    assert result.token == "ael_test_token"
    assert "INSERT INTO organizations" in sql
    assert "INSERT INTO principals" in sql
    assert "INSERT INTO organization_memberships" in sql
    assert "INSERT INTO api_credentials" in sql


def test_bootstrap_reuses_existing_access_records(monkeypatch):
    cursor = install_fake_database(
        monkeypatch,
        [
            (10, "active"),
            (20, "active"),
            ("active",),
        ],
    )

    result = run_bootstrap()
    sql = "\\n".join(cursor.statements)

    assert result.organization_id == 10
    assert result.principal_id == 20
    assert "INSERT INTO organizations" not in sql
    assert "INSERT INTO principals" not in sql
    assert "UPDATE organization_memberships" in sql
    assert "INSERT INTO api_credentials" in sql


def test_bootstrap_rejects_disabled_organization(monkeypatch):
    install_fake_database(
        monkeypatch,
        [(10, "disabled")],
    )

    with pytest.raises(
        module.BootstrapError,
        match="Organization exists but is disabled",
    ):
        run_bootstrap()


def test_parser_rejects_invalid_role():
    parser = module.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--display-name",
                "Owner",
                "--subject",
                "owner",
                "--role",
                "superuser",
            ]
        )


def test_bootstrap_rejects_production(monkeypatch):
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(app_env="production"),
    )

    with pytest.raises(
        module.BootstrapError,
        match="disabled in production",
    ):
        run_bootstrap()


def test_bootstrap_rejects_service_role(monkeypatch):
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(app_env="development"),
    )

    with pytest.raises(
        module.BootstrapError,
        match="Invalid bootstrap role",
    ):
        run_bootstrap(role="service")
