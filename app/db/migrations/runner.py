import argparse
import hashlib
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import psycopg

from app.db.migrations.manifest import (
    BASELINE_MAX_VERSION,
    BASELINE_MIGRATIONS,
)
from app.db.postgres import build_postgres_dsn


ADVISORY_LOCK_KEY = 290008001

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent
    / "sql"
)

MIGRATION_FILENAME_RE = re.compile(
    r"^(?P<version>\d{3})-"
    r"(?P<slug>[a-z0-9][a-z0-9-]*)"
    r"\.sql$"
)


EXPECTED_TABLES = frozenset(
    {
        "rag_documents",
        "rag_document_chunks",
        "organizations",
        "principals",
        "organization_memberships",
        "api_credentials",
        "organizational_units",
        "principal_unit_memberships",
        "rag_document_acl_entries",
    }
)


EXPECTED_COLUMN_MARKERS = frozenset(
    {
        (
            "rag_documents",
            "organization_id",
            "NO",
        ),
        (
            "rag_documents",
            "created_by_principal_id",
            "YES",
        ),
        (
            "rag_documents",
            "organizational_unit_id",
            "YES",
        ),
        (
            "rag_documents",
            "access_mode",
            "NO",
        ),
        (
            "organizational_units",
            "organization_id",
            "NO",
        ),
        (
            "organizational_units",
            "parent_unit_id",
            "YES",
        ),
        (
            "principal_unit_memberships",
            "organizational_unit_id",
            "NO",
        ),
        (
            "principal_unit_memberships",
            "principal_id",
            "NO",
        ),
        (
            "rag_document_acl_entries",
            "document_id",
            "NO",
        ),
        (
            "rag_document_acl_entries",
            "principal_id",
            "NO",
        ),
        (
            "rag_document_acl_entries",
            "permission",
            "NO",
        ),
    }
)


EXPECTED_CONSTRAINTS = frozenset(
    {
        (
            "rag_document_chunks",
            "rag_document_chunks_document_id_chunk_index_key",
        ),
        (
            "organizations",
            "organizations_slug_key",
        ),
        (
            "api_credentials",
            "api_credentials_secret_hash_key",
        ),
        (
            "rag_documents",
            "rag_documents_organization_id_fkey",
        ),
        (
            "rag_documents",
            "rag_documents_created_by_principal_id_fkey",
        ),
        (
            "organizational_units",
            "organizational_units_parent_same_org_fk",
        ),
        (
            "principal_unit_memberships",
            "principal_unit_memberships_org_membership_fk",
        ),
        (
            "rag_documents",
            "rag_documents_org_unit_fk",
        ),
        (
            "rag_documents",
            "rag_documents_access_mode_check",
        ),
        (
            "rag_documents",
            "rag_documents_org_id_key",
        ),
        (
            "rag_document_acl_entries",
            "rag_document_acl_entries_unique",
        ),
        (
            "rag_document_acl_entries",
            "rag_document_acl_entries_document_fk",
        ),
        (
            "rag_document_acl_entries",
            "rag_document_acl_entries_membership_fk",
        ),
        (
            "rag_document_acl_entries",
            "rag_document_acl_entries_organization_fk",
        ),
    }
)


SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version BIGINT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    checksum_sha256 CHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT schema_migrations_checksum_format
        CHECK (
            checksum_sha256 ~ '^[0-9a-f]{64}$'
        )
);
"""


class MigrationError(Exception):
    pass


@dataclass(frozen=True)
class BaselineSnapshot:
    vector_extension: bool
    tables: frozenset[str]
    columns: frozenset[tuple[str, str, str]]
    constraints: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class MigrationRecord:
    version: int
    name: str
    checksum_sha256: str


@dataclass(frozen=True)
class SqlMigration:
    version: int
    name: str
    path: Path
    checksum_sha256: str
    sql: str


def calculate_sha256(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def discover_sql_migrations(
    directory: Path = MIGRATIONS_DIR,
) -> tuple[SqlMigration, ...]:
    if not directory.exists():
        return ()

    migrations = []

    for path in sorted(
        directory.iterdir()
    ):
        if path.name == "README.md":
            continue

        if not path.is_file():
            continue

        if path.suffix != ".sql":
            continue

        match = MIGRATION_FILENAME_RE.fullmatch(
            path.name
        )

        if not match:
            raise MigrationError(
                "Invalid migration filename: "
                f"{path.name}"
            )

        version = int(
            match.group(
                "version"
            )
        )

        if version <= BASELINE_MAX_VERSION:
            raise MigrationError(
                "Runtime migrations must start "
                f"after version {BASELINE_MAX_VERSION}."
            )

        raw = path.read_bytes()

        migrations.append(
            SqlMigration(
                version=version,
                name=path.name,
                path=path,
                checksum_sha256=(
                    calculate_sha256(
                        raw
                    )
                ),
                sql=raw.decode(
                    "utf-8"
                ),
            )
        )

    versions = [
        migration.version
        for migration in migrations
    ]

    if len(versions) != len(
        set(versions)
    ):
        raise MigrationError(
            "Duplicate migration version."
        )

    if versions:
        expected = list(
            range(
                BASELINE_MAX_VERSION + 1,
                max(versions) + 1,
            )
        )

        if versions != expected:
            raise MigrationError(
                "Migration versions must be "
                "contiguous starting at "
                f"{BASELINE_MAX_VERSION + 1}."
            )

    return tuple(
        migrations
    )


def load_baseline_snapshot(
    connection,
) -> BaselineSnapshot:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_extension
                WHERE extname = 'vector'
            );
            """
        )

        vector_extension = bool(
            cursor.fetchone()[0]
        )

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public';
            """
        )

        tables = frozenset(
            row[0]
            for row in cursor.fetchall()
        )

        cursor.execute(
            """
            SELECT
                table_name,
                column_name,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public';
            """
        )

        columns = frozenset(
            (
                row[0],
                row[1],
                row[2],
            )
            for row in cursor.fetchall()
        )

        cursor.execute(
            """
            SELECT
                table_name,
                constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'public';
            """
        )

        constraints = frozenset(
            (
                row[0],
                row[1],
            )
            for row in cursor.fetchall()
        )

    return BaselineSnapshot(
        vector_extension=vector_extension,
        tables=tables,
        columns=columns,
        constraints=constraints,
    )


def validate_baseline_snapshot(
    snapshot: BaselineSnapshot,
) -> None:
    problems = []

    if not snapshot.vector_extension:
        problems.append(
            "vector extension missing"
        )

    missing_tables = sorted(
        EXPECTED_TABLES
        - snapshot.tables
    )

    if missing_tables:
        problems.append(
            "missing tables: "
            + ", ".join(
                missing_tables
            )
        )

    missing_columns = sorted(
        EXPECTED_COLUMN_MARKERS
        - snapshot.columns
    )

    if missing_columns:
        rendered = [
            (
                f"{table}.{column}"
                f"(nullable={nullable})"
            )
            for (
                table,
                column,
                nullable,
            ) in missing_columns
        ]

        problems.append(
            "missing column markers: "
            + ", ".join(rendered)
        )

    missing_constraints = sorted(
        EXPECTED_CONSTRAINTS
        - snapshot.constraints
    )

    if missing_constraints:
        rendered = [
            f"{table}.{constraint}"
            for (
                table,
                constraint,
            ) in missing_constraints
        ]

        problems.append(
            "missing constraints: "
            + ", ".join(rendered)
        )

    if problems:
        raise MigrationError(
            "Baseline verification failed: "
            + "; ".join(problems)
        )


def verify_baseline_schema(
    connection,
) -> None:
    validate_baseline_snapshot(
        load_baseline_snapshot(
            connection
        )
    )


def _metadata_table_exists(
    connection,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT (
                to_regclass(
                    'public.schema_migrations'
                )
                IS NOT NULL
            );
            """
        )

        return bool(
            cursor.fetchone()[0]
        )


def _ensure_metadata_table(
    connection,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            SCHEMA_MIGRATIONS_DDL
        )


def load_migration_records(
    connection,
) -> dict[int, MigrationRecord]:
    if not _metadata_table_exists(
        connection
    ):
        return {}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                version,
                name,
                TRIM(checksum_sha256)
            FROM schema_migrations
            ORDER BY version;
            """
        )

        return {
            int(version): MigrationRecord(
                version=int(version),
                name=name,
                checksum_sha256=checksum,
            )
            for (
                version,
                name,
                checksum,
            ) in cursor.fetchall()
        }


def validate_registered_baseline(
    records: dict[int, MigrationRecord],
) -> bool:
    expected_versions = {
        item.version
        for item in BASELINE_MIGRATIONS
    }

    found_versions = {
        version
        for version in records
        if version <= BASELINE_MAX_VERSION
    }

    if not found_versions:
        return False

    if (
        found_versions
        != expected_versions
    ):
        raise MigrationError(
            "Partial baseline registration "
            "detected."
        )

    for expected in BASELINE_MIGRATIONS:
        current = records[
            expected.version
        ]

        if current.name != expected.name:
            raise MigrationError(
                "Baseline migration name "
                "mismatch at version "
                f"{expected.version}."
            )

        if (
            current.checksum_sha256
            != expected.checksum_sha256
        ):
            raise MigrationError(
                "Baseline checksum mismatch "
                "at version "
                f"{expected.version}."
            )

    return True


def ensure_baseline_registered(
    connection,
) -> bool:
    verify_baseline_schema(
        connection
    )

    with connection.transaction():
        _ensure_metadata_table(
            connection
        )

        records = load_migration_records(
            connection
        )

        already_registered = (
            validate_registered_baseline(
                records
            )
        )

        if already_registered:
            return False

        if records:
            raise MigrationError(
                "Migration metadata exists "
                "without the required baseline."
            )

        with connection.cursor() as cursor:
            for item in BASELINE_MIGRATIONS:
                cursor.execute(
                    """
                    INSERT INTO schema_migrations (
                        version,
                        name,
                        checksum_sha256
                    )
                    VALUES (%s, %s, %s);
                    """,
                    (
                        item.version,
                        item.name,
                        item.checksum_sha256,
                    ),
                )

    return True


def validate_applied_history(
    records: dict[int, MigrationRecord],
    migrations: tuple[SqlMigration, ...],
) -> None:
    if not validate_registered_baseline(
        records
    ):
        raise MigrationError(
            "Baseline is not registered."
        )

    discovered = {
        migration.version: migration
        for migration in migrations
    }

    applied_future_versions = sorted(
        version
        for version in records
        if version > BASELINE_MAX_VERSION
    )

    expected_prefix = [
        migration.version
        for migration in migrations[
            : len(
                applied_future_versions
            )
        ]
    ]

    if (
        applied_future_versions
        != expected_prefix
    ):
        raise MigrationError(
            "Applied migration history is "
            "not a contiguous prefix of "
            "available migrations."
        )

    for version in applied_future_versions:
        migration = discovered.get(
            version
        )

        if migration is None:
            raise MigrationError(
                "Applied migration file is "
                "missing for version "
                f"{version}."
            )

        record = records[
            version
        ]

        if record.name != migration.name:
            raise MigrationError(
                "Migration name mismatch at "
                f"version {version}."
            )

        if (
            record.checksum_sha256
            != migration.checksum_sha256
        ):
            raise MigrationError(
                "Migration checksum mismatch "
                f"at version {version}."
            )


def apply_pending_migrations(
    connection,
) -> int:
    ensure_baseline_registered(
        connection
    )

    migrations = discover_sql_migrations()

    records = load_migration_records(
        connection
    )

    validate_applied_history(
        records,
        migrations,
    )

    applied = 0

    for migration in migrations:
        if migration.version in records:
            continue

        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    migration.sql,
                    prepare=False,
                )

                cursor.execute(
                    """
                    INSERT INTO schema_migrations (
                        version,
                        name,
                        checksum_sha256
                    )
                    VALUES (%s, %s, %s);
                    """,
                    (
                        migration.version,
                        migration.name,
                        migration.checksum_sha256,
                    ),
                )

        applied += 1

    return applied


def _connect():
    return psycopg.connect(
        build_postgres_dsn(),
        connect_timeout=5,
        autocommit=True,
    )


@contextmanager
def locked_connection():
    connection = _connect()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_try_advisory_lock(%s);",
                (
                    ADVISORY_LOCK_KEY,
                ),
            )

            locked = bool(
                cursor.fetchone()[0]
            )

        if not locked:
            raise MigrationError(
                "Another migration runner "
                "holds the advisory lock."
            )

        try:
            yield connection

        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(%s);",
                    (
                        ADVISORY_LOCK_KEY,
                    ),
                )

    finally:
        connection.close()


def command_verify() -> None:
    with _connect() as connection:
        verify_baseline_schema(
            connection
        )

    print(
        "baseline_schema: valid"
    )


def command_baseline() -> None:
    with locked_connection() as connection:
        created = (
            ensure_baseline_registered(
                connection
            )
        )

    print(
        "baseline_registration:",
        (
            "created"
            if created
            else "already_registered"
        ),
    )


def command_apply() -> None:
    with locked_connection() as connection:
        applied = (
            apply_pending_migrations(
                connection
            )
        )

    print(
        f"migrations_applied: {applied}"
    )


def command_status() -> None:
    with _connect() as connection:
        verify_baseline_schema(
            connection
        )

        records = load_migration_records(
            connection
        )

        migrations = (
            discover_sql_migrations()
        )

        if not records:
            print(
                "baseline_schema: valid"
            )
            print(
                "schema_migrations: absent"
            )
            print(
                "future_migrations_available:",
                len(migrations),
            )
            return

        validate_applied_history(
            records,
            migrations,
        )

        applied_future = [
            version
            for version in records
            if version > BASELINE_MAX_VERSION
        ]

        pending = [
            migration.version
            for migration in migrations
            if migration.version not in records
        ]

        print(
            "baseline_schema: valid"
        )
        print(
            "baseline_registration: valid"
        )
        print(
            "future_migrations_applied:",
            len(applied_future),
        )
        print(
            "future_migrations_pending:",
            len(pending),
        )

        if pending:
            print(
                "pending_versions:",
                ",".join(
                    str(version)
                    for version in pending
                ),
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "AI Enterprise Lab database "
            "migration runner."
        )
    )

    parser.add_argument(
        "command",
        choices=(
            "verify",
            "baseline",
            "status",
            "apply",
        ),
    )

    return parser


def main(
    argv=None,
) -> int:
    parser = build_parser()

    args = parser.parse_args(
        argv
    )

    commands = {
        "verify": command_verify,
        "baseline": command_baseline,
        "status": command_status,
        "apply": command_apply,
    }

    try:
        commands[
            args.command
        ]()

    except (
        MigrationError,
        psycopg.Error,
        OSError,
    ) as exc:
        print(
            "migration_error:",
            str(exc),
            file=sys.stderr,
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
