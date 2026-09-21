from pathlib import Path

import pytest

from app.db.migrations.manifest import (
    BASELINE_MIGRATIONS,
)
from app.db.migrations.runner import (
    EXPECTED_COLUMN_MARKERS,
    EXPECTED_CONSTRAINTS,
    EXPECTED_TABLES,
    BaselineSnapshot,
    MigrationError,
    MigrationRecord,
    calculate_sha256,
    discover_sql_migrations,
    locked_connection,
    validate_baseline_snapshot,
    validate_registered_baseline,
)


def valid_snapshot():
    return BaselineSnapshot(
        vector_extension=True,
        tables=(
            EXPECTED_TABLES
            | {"lab_vectors"}
        ),
        columns=EXPECTED_COLUMN_MARKERS,
        constraints=EXPECTED_CONSTRAINTS,
    )


def baseline_records():
    return {
        item.version: MigrationRecord(
            version=item.version,
            name=item.name,
            checksum_sha256=(
                item.checksum_sha256
            ),
        )
        for item in BASELINE_MIGRATIONS
    }


def test_baseline_manifest_versions_are_frozen():
    assert [
        item.version
        for item in BASELINE_MIGRATIONS
    ] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_baseline_manifest_checksums_are_sha256():
    for item in BASELINE_MIGRATIONS:
        assert len(
            item.checksum_sha256
        ) == 64

        int(
            item.checksum_sha256,
            16,
        )


def test_valid_baseline_snapshot_passes():
    validate_baseline_snapshot(
        valid_snapshot()
    )


def test_missing_baseline_table_fails_closed():
    snapshot = valid_snapshot()

    broken = BaselineSnapshot(
        vector_extension=True,
        tables=(
            snapshot.tables
            - {"rag_document_acl_entries"}
        ),
        columns=snapshot.columns,
        constraints=snapshot.constraints,
    )

    with pytest.raises(
        MigrationError,
        match="missing tables",
    ):
        validate_baseline_snapshot(
            broken
        )


def test_missing_baseline_column_fails_closed():
    snapshot = valid_snapshot()

    marker = (
        "rag_documents",
        "access_mode",
        "NO",
    )

    broken = BaselineSnapshot(
        vector_extension=True,
        tables=snapshot.tables,
        columns=(
            snapshot.columns
            - {marker}
        ),
        constraints=snapshot.constraints,
    )

    with pytest.raises(
        MigrationError,
        match="missing column markers",
    ):
        validate_baseline_snapshot(
            broken
        )


def test_missing_constraint_fails_closed():
    snapshot = valid_snapshot()

    marker = (
        "rag_documents",
        "rag_documents_access_mode_check",
    )

    broken = BaselineSnapshot(
        vector_extension=True,
        tables=snapshot.tables,
        columns=snapshot.columns,
        constraints=(
            snapshot.constraints
            - {marker}
        ),
    )

    with pytest.raises(
        MigrationError,
        match="missing constraints",
    ):
        validate_baseline_snapshot(
            broken
        )


def test_registered_baseline_passes():
    assert (
        validate_registered_baseline(
            baseline_records()
        )
        is True
    )


def test_partial_registered_baseline_fails():
    records = baseline_records()

    records.pop(6)

    with pytest.raises(
        MigrationError,
        match="Partial baseline",
    ):
        validate_registered_baseline(
            records
        )


def test_changed_baseline_checksum_fails():
    records = baseline_records()

    item = records[6]

    records[6] = MigrationRecord(
        version=item.version,
        name=item.name,
        checksum_sha256=(
            "0" * 64
        ),
    )

    with pytest.raises(
        MigrationError,
        match="checksum mismatch",
    ):
        validate_registered_baseline(
            records
        )


def test_discovery_accepts_contiguous_007(
    tmp_path: Path,
):
    sql = (
        b"CREATE TABLE migration_test "
        b"(id BIGINT PRIMARY KEY);\n"
    )

    path = (
        tmp_path
        / "007-create-migration-test.sql"
    )

    path.write_bytes(
        sql
    )

    migrations = (
        discover_sql_migrations(
            tmp_path
        )
    )

    assert len(
        migrations
    ) == 1

    assert (
        migrations[0].version
        == 7
    )

    assert (
        migrations[0].checksum_sha256
        == calculate_sha256(sql)
    )


def test_discovery_rejects_gap(
    tmp_path: Path,
):
    (
        tmp_path
        / "008-gap.sql"
    ).write_text(
        "SELECT 1;\n",
        encoding="utf-8",
    )

    with pytest.raises(
        MigrationError,
        match="contiguous",
    ):
        discover_sql_migrations(
            tmp_path
        )


def test_discovery_rejects_baseline_version(
    tmp_path: Path,
):
    (
        tmp_path
        / "006-forbidden.sql"
    ).write_text(
        "SELECT 1;\n",
        encoding="utf-8",
    )

    with pytest.raises(
        MigrationError,
        match="must start",
    ):
        discover_sql_migrations(
            tmp_path
        )

def test_baseline_manifest_matches_bootstrap_files():
    root = Path(__file__).resolve().parents[1]

    bootstrap_dir = (
        root
        / "infra"
        / "postgres"
        / "init"
    )

    for item in BASELINE_MIGRATIONS:
        path = (
            bootstrap_dir
            / item.name
        )

        assert path.is_file()

        assert (
            calculate_sha256(
                path.read_bytes()
            )
            == item.checksum_sha256
        )


def test_advisory_lock_contention_fails_fast(
    monkeypatch,
):
    class Cursor:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False

        def execute(
            self,
            query,
            params=None,
        ):
            self.query = query

        def fetchone(self):
            assert (
                "pg_try_advisory_lock"
                in self.query
            )

            return (False,)

    class Connection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            return Cursor()

        def close(self):
            self.closed = True

    connection = Connection()

    monkeypatch.setattr(
        "app.db.migrations.runner._connect",
        lambda: connection,
    )

    with pytest.raises(
        MigrationError,
        match="Another migration runner",
    ):
        with locked_connection():
            pass

    assert connection.closed is True
