import asyncio

import pytest
from fastapi import HTTPException

from app.rate_limit import http
from app.rate_limit.limiter import (
    RateLimitUnavailableError,
)
from app.rate_limit.models import (
    RateLimitDecision,
)


def test_allowed_request_is_returned(
    monkeypatch,
):
    captured = {}

    async def fake_consume_token(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return RateLimitDecision(
            allowed=True,
            remaining=4,
            retry_after_seconds=0,
        )

    monkeypatch.setattr(
        http,
        "consume_token",
        fake_consume_token,
    )

    result = asyncio.run(
        http.enforce_rate_limit(
            key="rate-limit:test",
            rate_per_minute=30,
            burst=5,
        )
    )

    assert result.allowed is True
    assert result.remaining == 4

    assert captured == {
        "key": "rate-limit:test",
        "rate_per_minute": 30,
        "burst": 5,
    }


def test_denied_request_returns_429(
    monkeypatch,
):
    async def fake_consume_token(
        **kwargs,
    ):
        return RateLimitDecision(
            allowed=False,
            remaining=0,
            retry_after_seconds=7,
        )

    monkeypatch.setattr(
        http,
        "consume_token",
        fake_consume_token,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            http.enforce_rate_limit(
                key="rate-limit:test",
                rate_per_minute=30,
                burst=5,
            )
        )

    exc = exc_info.value

    assert exc.status_code == 429

    assert exc.detail == (
        "Rate limit exceeded."
    )

    assert exc.headers == {
        "Retry-After": "7"
    }


def test_backend_unavailable_returns_503(
    monkeypatch,
):
    async def fake_consume_token(
        **kwargs,
    ):
        raise RateLimitUnavailableError(
            "internal redis detail"
        )

    monkeypatch.setattr(
        http,
        "consume_token",
        fake_consume_token,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            http.enforce_rate_limit(
                key="rate-limit:test",
                rate_per_minute=30,
                burst=5,
            )
        )

    exc = exc_info.value

    assert exc.status_code == 503

    assert exc.detail == (
        "Rate limit service unavailable."
    )

    assert (
        "internal redis detail"
        not in str(
            exc.detail
        )
    )