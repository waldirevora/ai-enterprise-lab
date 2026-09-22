import argparse
import asyncio
import sys
from dataclasses import dataclass

import psycopg

from app.access.api_keys import generate_api_key
from app.db.postgres import DatabaseConnectionError, build_postgres_dsn


class BootstrapError(Exception):
    pass


@dataclass(frozen=True)
class BootstrapResult:
    organization_id: int
    principal_id: int
    key_prefix: str
    token: str


async def bootstrap_access(
    *,
    organization_slug: str,
    organization_name: str,
    display_name: str,
    subject: str,
    role: str,
    max_classification: str,
    credential_name: str,
) -> BootstrapResult:
    organization_slug = organization_slug.strip()
    organization_name = organization_name.strip()
    display_name = display_name.strip()
    subject = subject.strip()
    credential_name = credential_name.strip()

    if not all((
        organization_slug,
        organization_name,
        display_name,
        subject,
        credential_name,
    )):
        raise BootstrapError("Bootstrap values cannot be empty.")

    external_subject = f"{organization_slug}:{subject}"

    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT id, status
                FROM organizations
                WHERE slug = %s;
                """,
                (organization_slug,),
            )
            organization = await cursor.fetchone()

            if organization is None:
                await cursor.execute(
                    """
                    INSERT INTO organizations (slug, name)
                    VALUES (%s, %s)
                    RETURNING id;
                    """,
                    (organization_slug, organization_name),
                )
                organization_id = (await cursor.fetchone())[0]
            else:
                organization_id, organization_status = organization
                if organization_status != "active":
                    raise BootstrapError(
                        "Organization exists but is disabled."
                    )

            await cursor.execute(
                """
                SELECT id, status
                FROM principals
                WHERE auth_provider = %s
                  AND external_subject = %s;
                """,
                ("local-bootstrap", external_subject),
            )
            principal = await cursor.fetchone()

            if principal is None:
                await cursor.execute(
                    """
                    INSERT INTO principals (
                        kind,
                        display_name,
                        auth_provider,
                        external_subject
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        "user",
                        display_name,
                        "local-bootstrap",
                        external_subject,
                    ),
                )
                principal_id = (await cursor.fetchone())[0]
            else:
                principal_id, principal_status = principal
                if principal_status != "active":
                    raise BootstrapError(
                        "Principal exists but is disabled."
                    )

            await cursor.execute(
                """
                SELECT status
                FROM organization_memberships
                WHERE organization_id = %s
                  AND principal_id = %s;
                """,
                (organization_id, principal_id),
            )
            membership = await cursor.fetchone()
            if membership is None:
                await cursor.execute(
                    """
                    INSERT INTO organization_memberships (
                        organization_id,
                        principal_id,
                        role,
                        max_classification
                    )
                    VALUES (%s, %s, %s, %s);
                    """,
                    (
                        organization_id,
                        principal_id,
                        role,
                        max_classification,
                    ),
                )
            else:
                if membership[0] != "active":
                    raise BootstrapError(
                        "Membership exists but is disabled."
                    )

                await cursor.execute(
                    """
                    UPDATE organization_memberships
                    SET role = %s,
                        max_classification = %s,
                        updated_at = NOW()
                    WHERE organization_id = %s
                      AND principal_id = %s;
                    """,
                    (
                        role,
                        max_classification,
                        organization_id,
                        principal_id,
                    ),
                )

            generated = generate_api_key()

            await cursor.execute(
                """
                INSERT INTO api_credentials (
                    organization_id,
                    principal_id,
                    name,
                    key_prefix,
                    secret_hash
                )
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    organization_id,
                    principal_id,
                    credential_name,
                    generated.key_prefix,
                    generated.secret_hash,
                ),
            )

    return BootstrapResult(
        organization_id=organization_id,
        principal_id=principal_id,
        key_prefix=generated.key_prefix,
        token=generated.token,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap an AI Enterprise Lab API credential."
    )
    parser.add_argument("--organization-slug", default="lab-default")
    parser.add_argument("--organization-name", default="AI Enterprise Lab")
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument(
        "--role",
        choices=("owner", "admin", "member", "service"),
        default="owner",
    )
    parser.add_argument(
        "--max-classification",
        choices=("public", "internal", "confidential"),
        default="internal",
    )
    parser.add_argument("--credential-name", default="quickstart")
    return parser


async def _run(args: argparse.Namespace) -> int:
    result = await bootstrap_access(
        organization_slug=args.organization_slug,
        organization_name=args.organization_name,
        display_name=args.display_name,
        subject=args.subject,
        role=args.role,
        max_classification=args.max_classification,
        credential_name=args.credential_name,
    )

    print("BOOTSTRAP_ACCESS=PASS")
    print(f"organization_id={result.organization_id}")
    print(f"principal_id={result.principal_id}")
    print(f"key_prefix={result.key_prefix}")
    print("API key is shown once. Store it securely.")
    print(f"api_key={result.token}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(_run(args))
    except (
        BootstrapError,
        DatabaseConnectionError,
        psycopg.Error,
    ) as exc:
        print(f"BOOTSTRAP_ACCESS=FAIL error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
