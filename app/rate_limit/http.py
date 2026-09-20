from fastapi import (
    HTTPException,
    status,
)

from app.audit.logger import emit_audit_event
from app.observability.metrics import (
    RATE_LIMIT_EVENTS_TOTAL,
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
        emit_audit_event(
            event_type=(
                "rate_limit.unavailable"
            ),
            outcome="unavailable",
            reason_code=(
                "rate_limit_backend_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        RATE_LIMIT_EVENTS_TOTAL.labels(
            outcome="unavailable",
        ).inc()

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Rate limit service unavailable."
            ),
        ) from exc

    if not decision.allowed:
        emit_audit_event(
            event_type=(
                "rate_limit.denied"
            ),
            outcome="denied",
            reason_code=(
                "rate_limit_exceeded"
            ),
            metadata={
                "status_code": 429,
                "retry_after_seconds": (
                    decision.retry_after_seconds
                ),
            },
        )

        RATE_LIMIT_EVENTS_TOTAL.labels(
            outcome="rate_limited",
        ).inc()

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
