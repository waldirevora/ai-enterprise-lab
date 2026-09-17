import math

from app.core.config import settings
from app.rate_limit.backend import (
    RateLimitBackendError,
    backend,
)
from app.rate_limit.models import (
    RateLimitDecision,
)


class RateLimitConfigurationError(Exception):
    pass


class RateLimitUnavailableError(Exception):
    pass


_TOKEN_BUCKET_SCRIPT = r"""
local key = KEYS[1]

local rate_per_minute = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])

if not rate_per_minute
   or rate_per_minute <= 0
   or not capacity
   or capacity <= 0 then
    return redis.error_reply(
        "invalid rate limit configuration"
    )
end

local redis_time = redis.call("TIME")

local now_ms =
    (tonumber(redis_time[1]) * 1000)
    + math.floor(
        tonumber(redis_time[2]) / 1000
    )

local rate_per_ms =
    rate_per_minute / 60000

local state = redis.call(
    "HMGET",
    key,
    "tokens",
    "timestamp_ms"
)

local tokens = tonumber(state[1])
local timestamp_ms = tonumber(state[2])

if not tokens or not timestamp_ms then
    tokens = capacity
    timestamp_ms = now_ms
end

local elapsed_ms =
    math.max(
        0,
        now_ms - timestamp_ms
    )

tokens = math.min(
    capacity,
    tokens
        + (
            elapsed_ms
            * rate_per_ms
        )
)

local allowed = 0
local retry_after_ms = 0

if tokens >= 1 then
    allowed = 1
    tokens = tokens - 1
else
    local missing_tokens =
        1 - tokens

    retry_after_ms = math.ceil(
        missing_tokens
        / rate_per_ms
    )
end

redis.call(
    "HSET",
    key,
    "tokens",
    tostring(tokens),
    "timestamp_ms",
    tostring(now_ms)
)

local full_refill_ms = math.ceil(
    capacity
    / rate_per_ms
)

redis.call(
    "PEXPIRE",
    key,
    math.max(
        1000,
        full_refill_ms
    )
)

local remaining = math.floor(tokens)

return {
    allowed,
    remaining,
    retry_after_ms
}
"""


def _validate_configuration(
    *,
    key: str,
    rate_per_minute: int,
    burst: int,
) -> None:
    if not key.strip():
        raise RateLimitConfigurationError(
            "Rate limit key must not be empty."
        )

    if rate_per_minute < 1:
        raise RateLimitConfigurationError(
            "rate_per_minute must be "
            "a positive integer."
        )

    if burst < 1:
        raise RateLimitConfigurationError(
            "burst must be a positive integer."
        )


async def consume_token(
    *,
    key: str,
    rate_per_minute: int,
    burst: int,
) -> RateLimitDecision:
    _validate_configuration(
        key=key,
        rate_per_minute=rate_per_minute,
        burst=burst,
    )

    if not settings.rate_limit_enabled:
        return RateLimitDecision(
            allowed=True,
            remaining=burst,
            retry_after_seconds=0,
        )

    try:
        result = await backend.execute(
            script=_TOKEN_BUCKET_SCRIPT,
            key=key,
            args=[
                rate_per_minute,
                burst,
            ],
        )

    except RateLimitBackendError as exc:
        raise RateLimitUnavailableError(
            "Rate limit service unavailable."
        ) from exc

    allowed = result[0] == 1

    remaining = max(
        0,
        result[1],
    )

    retry_after_ms = max(
        0,
        result[2],
    )

    retry_after_seconds = (
        0
        if allowed
        else max(
            1,
            math.ceil(
                retry_after_ms
                / 1000
            ),
        )
    )

    return RateLimitDecision(
        allowed=allowed,
        remaining=remaining,
        retry_after_seconds=(
            retry_after_seconds
        ),
    )