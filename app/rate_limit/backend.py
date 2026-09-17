from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class RateLimitBackendError(Exception):
    pass


class RedisRateLimitBackend:
    def __init__(
        self,
        client: Redis | None = None,
    ) -> None:
        self._client = (
            client
            if client is not None
            else Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=(
                    settings.redis_password
                    or None
                ),
                socket_connect_timeout=(
                    settings.redis_connect_timeout_seconds
                ),
                socket_timeout=(
                    settings.redis_socket_timeout_seconds
                ),
                decode_responses=True,
            )
        )

    async def execute(
        self,
        *,
        script: str,
        key: str,
        args: list[Any],
    ) -> list[int]:
        try:
            result = await self._client.eval(
                script,
                1,
                key,
                *args,
            )

        except (
            RedisError,
            OSError,
        ) as exc:
            raise RateLimitBackendError(
                "Rate limit backend unavailable."
            ) from exc

        if (
            not isinstance(result, list)
            or len(result) != 3
        ):
            raise RateLimitBackendError(
                "Invalid rate limit backend response."
            )

        try:
            return [
                int(result[0]),
                int(result[1]),
                int(result[2]),
            ]

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise RateLimitBackendError(
                "Invalid rate limit backend response."
            ) from exc

    async def close(self) -> None:
        await self._client.aclose()


backend = RedisRateLimitBackend()