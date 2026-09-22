import asyncio
import os
import sys
from dataclasses import dataclass

import psycopg

from app.access.api_keys import (
    ApiKeyError,
    extract_key_prefix,
    hash_api_key,
)
from app.db.postgres import (
    DatabaseConnectionError,
    build_postgres_dsn,
)


class RevokeApiKeyError(Exception):
    pass


@dataclass(frozen=True)
class RevokeApiKeyResult:
    credential_id: int
    key_prefix: str
    already_revoked: bool


def _read_api_key() -> str:
    token = os.environ.get("AEL_API_KEY", "").strip()
    if not token:
        raise RevokeApiKeyError(
            "AEL_API_KEY is not configured."
        )
    return token


async def revoke_api_key(token: str) -> RevokeApiKeyResult:
    token = token.strip()

    if not token:
        raise RevokeApiKeyError("API key cannot be empty.")

    try:
        key_prefix = extract_key_prefix(token)
        secret_hash = hash_api_key(token)
    except ApiKeyError as exc:
        raise RevokeApiKeyError(
            "Invalid API key format."
        ) from exc

    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE api_credentials
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE key_prefix = %s
                  AND secret_hash = %s
                  AND revoked_at IS NULL
                RETURNING id, key_prefix;
                """,
                (key_prefix, secret_hash),
            )
            row = await cursor.fetchone()

            if row is not None:
                return RevokeApiKeyResult(
                    credential_id=row[0],
                    key_prefix=row[1],
                    already_revoked=False,
                )

            await cursor.execute(
                """
                SELECT id, key_prefix, revoked_at
                FROM api_credentials
                WHERE key_prefix = %s
                  AND secret_hash = %s
                ORDER BY id
                LIMIT 1;
                """,
                (key_prefix, secret_hash),
            )
            existing = await cursor.fetchone()

    if existing is None:
        raise RevokeApiKeyError(
            "API credential was not found."
        )

    return RevokeApiKeyResult(
        credential_id=existing[0],
        key_prefix=existing[1],
        already_revoked=existing[2] is not None,
    )


async def _run() -> int:
    result = await revoke_api_key(_read_api_key())

    print("REVOKE_API_KEY=PASS")
    print(f"credential_id={result.credential_id}")
    print(f"key_prefix={result.key_prefix}")
    print(
        "already_revoked="
        + str(result.already_revoked).lower()
    )
    return 0


def main() -> int:
    try:
        return asyncio.run(_run())
    except (
        RevokeApiKeyError,
        DatabaseConnectionError,
        psycopg.Error,
    ) as exc:
        print(f"REVOKE_API_KEY=FAIL error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
