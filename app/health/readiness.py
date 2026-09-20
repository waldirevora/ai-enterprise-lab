from app.core.config import settings
from app.db.postgres import (
    DatabaseConnectionError,
    check_database_connection,
)
from app.rate_limit.backend import (
    RateLimitBackendError,
    backend,
)


class ReadinessCheckError(Exception):
    pass


async def check_readiness() -> bool:
    try:
        database_ready = (
            await check_database_connection()
        )

    except DatabaseConnectionError as exc:
        raise ReadinessCheckError(
            "Required dependency unavailable."
        ) from exc

    if not database_ready:
        raise ReadinessCheckError(
            "Required dependency unavailable."
        )

    if not settings.rate_limit_enabled:
        return True

    try:
        redis_ready = (
            await backend.check_connection()
        )

    except RateLimitBackendError as exc:
        raise ReadinessCheckError(
            "Required dependency unavailable."
        ) from exc

    if not redis_ready:
        raise ReadinessCheckError(
            "Required dependency unavailable."
        )

    return True
