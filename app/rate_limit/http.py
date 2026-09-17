from fastapi import (
    HTTPException,
    status,
)

from app.rate_limit.limiter import (
    RateLimitUnavailableError,
    consume_token,
)
from app.rate_limit.models import (
    RateLimitDecision,
)


async def enforce_rate_limit(
    *,
    key: str,
    rate_per_minute: int,
    burst: int,
) -> RateLimitDecision:
    try:
        decision = await consume_token(
            key=key,
            rate_per_minute=rate_per_minute,
            burst=burst,
        )

    except RateLimitUnavailableError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Rate limit service unavailable."
            ),
        ) from exc

    if not decision.allowed:
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail="Rate limit exceeded.",
            headers={
                "Retry-After": str(
                    decision.retry_after_seconds
                ),
            },
        )

    return decision