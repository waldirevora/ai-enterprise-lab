from dataclasses import dataclass

import psycopg

from app.access.api_keys import (
    ApiKeyError,
    extract_key_prefix,
    verify_api_key,
)
from app.access.context import (
    PrincipalContext,
    PrincipalContextError,
)
from app.db.postgres import build_postgres_dsn


class AuthenticationError(Exception):
    pass


class AuthenticationUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class CredentialCandidate:
    credential_id: int
    secret_hash: str

    principal_id: int
    principal_kind: str

    organization_id: int
    organization_slug: str

    role: str
    max_classification: str

    is_revoked: bool
    is_expired: bool

    principal_active: bool
    organization_active: bool
    membership_active: bool


async def _load_candidate_credentials(
    *,
    key_prefix: str,
) -> list[CredentialCandidate]:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    c.id,
                    c.secret_hash,

                    p.id,
                    p.kind,

                    o.id,
                    o.slug,

                    m.role,
                    m.max_classification,

                    (
                        c.revoked_at IS NOT NULL
                    ) AS is_revoked,

                    (
                        c.expires_at IS NOT NULL
                        AND c.expires_at
                            <= CURRENT_TIMESTAMP
                    ) AS is_expired,

                    (
                        p.status = 'active'
                    ) AS principal_active,

                    (
                        o.status = 'active'
                    ) AS organization_active,

                    (
                        m.status = 'active'
                    ) AS membership_active

                FROM api_credentials c

                JOIN principals p
                    ON p.id = c.principal_id

                JOIN organizations o
                    ON o.id = c.organization_id

                JOIN organization_memberships m
                    ON m.organization_id
                        = c.organization_id
                    AND m.principal_id
                        = c.principal_id

                WHERE c.key_prefix = %s

                ORDER BY c.id;
                """,
                (
                    key_prefix,
                ),
            )

            rows = await cursor.fetchall()

    return [
        CredentialCandidate(
            credential_id=row[0],
            secret_hash=row[1],
            principal_id=row[2],
            principal_kind=row[3],
            organization_id=row[4],
            organization_slug=row[5],
            role=row[6],
            max_classification=row[7],
            is_revoked=row[8],
            is_expired=row[9],
            principal_active=row[10],
            organization_active=row[11],
            membership_active=row[12],
        )
        for row in rows
    ]


async def _mark_credential_used(
    *,
    credential_id: int,
) -> bool:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE api_credentials AS c

                SET last_used_at = CURRENT_TIMESTAMP

                WHERE c.id = %s

                  AND c.revoked_at IS NULL

                  AND (
                      c.expires_at IS NULL
                      OR c.expires_at
                          > CURRENT_TIMESTAMP
                  )

                  AND EXISTS (
                      SELECT 1

                      FROM principals p

                      JOIN organizations o
                          ON o.id
                              = c.organization_id

                      JOIN organization_memberships m
                          ON m.organization_id
                              = c.organization_id
                          AND m.principal_id
                              = c.principal_id

                      WHERE p.id
                          = c.principal_id

                        AND p.status
                            = 'active'

                        AND o.status
                            = 'active'

                        AND m.status
                            = 'active'
                  )

                RETURNING c.id;
                """,
                (
                    credential_id,
                ),
            )

            row = await cursor.fetchone()

    return row is not None


def _credential_is_active(
    candidate: CredentialCandidate,
) -> bool:
    return (
        not candidate.is_revoked
        and not candidate.is_expired
        and candidate.principal_active
        and candidate.organization_active
        and candidate.membership_active
    )


async def authenticate_api_key(
    token: str,
) -> PrincipalContext:
    try:
        key_prefix = extract_key_prefix(
            token
        )

    except ApiKeyError as exc:
        raise AuthenticationError(
            "Invalid API credential."
        ) from exc

    try:
        candidates = (
            await _load_candidate_credentials(
                key_prefix=key_prefix,
            )
        )

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise AuthenticationUnavailableError(
            "Authentication service unavailable."
        ) from exc

    matching_candidate = None

    for candidate in candidates:
        if verify_api_key(
            token,
            candidate.secret_hash,
        ):
            matching_candidate = candidate
            break

    if matching_candidate is None:
        raise AuthenticationError(
            "Invalid API credential."
        )

    if not _credential_is_active(
        matching_candidate
    ):
        raise AuthenticationError(
            "Invalid API credential."
        )

    try:
        context = PrincipalContext(
            principal_id=(
                matching_candidate.principal_id
            ),
            organization_id=(
                matching_candidate.organization_id
            ),
            organization_slug=(
                matching_candidate.organization_slug
            ),
            principal_kind=(
                matching_candidate.principal_kind
            ),
            role=matching_candidate.role,
            max_classification=(
                matching_candidate.max_classification
            ),
        )

    except PrincipalContextError as exc:
        raise AuthenticationUnavailableError(
            "Authentication service unavailable."
        ) from exc

    try:
        credential_still_valid = (
            await _mark_credential_used(
                credential_id=(
                    matching_candidate.credential_id
                ),
            )
        )

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise AuthenticationUnavailableError(
            "Authentication service unavailable."
        ) from exc

    if not credential_still_valid:
        raise AuthenticationError(
            "Invalid API credential."
        )

    return context