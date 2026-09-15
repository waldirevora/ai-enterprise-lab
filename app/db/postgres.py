import psycopg

from app.core.config import settings


class DatabaseConnectionError(Exception):
    pass


def build_postgres_dsn() -> str:
    if not settings.postgres_password:
        raise DatabaseConnectionError(
            "PostgreSQL password is not configured."
        )

    return (
        f"host={settings.postgres_host} "
        f"port={settings.postgres_port} "
        f"dbname={settings.postgres_db} "
        f"user={settings.postgres_user} "
        f"password={settings.postgres_password}"
    )


async def check_database_connection() -> bool:
    try:
        async with await psycopg.AsyncConnection.connect(
            build_postgres_dsn(),
            connect_timeout=5,
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT 1;"
                )

                result = await cursor.fetchone()

        return result == (1,)

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise DatabaseConnectionError(
            "Could not connect to PostgreSQL."
        ) from exc