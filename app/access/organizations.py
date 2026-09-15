import psycopg

from app.db.postgres import build_postgres_dsn


class OrganizationResolutionError(Exception):
    pass


async def resolve_organization_id(
    slug: str,
) -> int:
    normalized_slug = slug.strip()

    if not normalized_slug:
        raise OrganizationResolutionError(
            "Organization slug is empty."
        )

    try:
        async with await psycopg.AsyncConnection.connect(
            build_postgres_dsn(),
            connect_timeout=5,
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id
                    FROM organizations
                    WHERE slug = %s
                      AND status = 'active';
                    """,
                    (normalized_slug,),
                )

                row = await cursor.fetchone()

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise OrganizationResolutionError(
            "Could not resolve organization."
        ) from exc

    if row is None:
        raise OrganizationResolutionError(
            "Organization was not found or is disabled."
        )

    return row[0]