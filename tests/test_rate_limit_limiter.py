import asyncio

import pytest

from app.rate_limit import limiter
from app.rate_limit.backend import (
    RateLimitBackendError,
)
from app.rate_limit.limiter import (
    RateLimitConfigurationError,
    RateLimitUnavailableError,
    consume_token,
)


def test_empty_key_is_rejected():
    with pytest.raises(
        RateLimitConfigurationError,
        match=(
            "Rate limit key must not be empty"
        ),
    ):
        asyncio.run(
            consume_token(
                key="   ",
                rate_per_minute=10,
                burst=2,
            )
        )


def test_invalid_rate_is_rejected():
    with pytest.raises(
        RateLimitConfigurationError,
        match=(
            "rate_per_minute must be "
            "a positive integer"
        ),
    ):
        asyncio.run(
            consume_token(
                key="test",
                rate_per_minute=0,
                burst=2,
            )
        )


def test_invalid_burst_is_rejected():
    with pytest.raises(
        RateLimitConfigurationError,
        match=(
            "burst must be a positive integer"
        ),
    ):
        asyncio.run(
            consume_token(
                key="test",
                rate_per_minute=10,
                burst=0,
            )
        )


def test_disabled_rate_limit_bypasses_backend(
    monkeypatch,
):
    async def should_not_execute(
        **kwargs,
    ):
        raise AssertionError(
            "Redis must not be called."
        )

    monkeypatch.setattr(
        limiter.settings,
        "rate_limit_enabled",
        False,
    )

    monkeypatch.setattr(
        limiter.backend,
        "execute",
        should_not_execute,
    )

    result = asyncio.run(
        consume_token(
            key="test",
            rate_per_minute=10,
            burst=3,
        )
    )

    assert result.allowed is True
    assert result.remaining == 3

    assert (
        result.retry_after_seconds
        == 0
    )


def test_allowed_decision_is_mapped(
    monkeypatch,
):
    captured = {}

    async def fake_execute(
        **kwargs,
    ):
        captured.update(kwargs)

        return [
            1,
            2,
            0,
        ]

    monkeypatch.setattr(
        limiter.backend,
        "execute",
        fake_execute,
    )

    result = asyncio.run(
        consume_token(
            key="rate-limit:test",
            rate_per_minute=12,
            burst=3,
        )
    )

    assert result.allowed is True
    assert result.remaining == 2

    assert (
        result.retry_after_seconds
        == 0
    )

    assert (
        captured["key"]
        == "rate-limit:test"
    )

    assert captured["args"] == [
        12,
        3,
    ]


def test_denied_decision_calculates_retry_after(
    monkeypatch,
):
    async def fake_execute(
        **kwargs,
    ):
        return [
            0,
            0,
            1501,
        ]

    monkeypatch.setattr(
        limiter.backend,
        "execute",
        fake_execute,
    )

    result = asyncio.run(
        consume_token(
            key="rate-limit:test",
            rate_per_minute=12,
            burst=3,
        )
    )

    assert result.allowed is False
    assert result.remaining == 0

    assert (
        result.retry_after_seconds
        == 2
    )


def test_backend_failure_is_sanitized(
    monkeypatch,
):
    async def fake_execute(
        **kwargs,
    ):
        raise RateLimitBackendError(
            "internal redis detail"
        )

    monkeypatch.setattr(
        limiter.backend,
        "execute",
        fake_execute,
    )

    with pytest.raises(
        RateLimitUnavailableError,
        match=(
            "Rate limit service unavailable"
        ),
    ) as exc_info:
        asyncio.run(
            consume_token(
                key="rate-limit:test",
                rate_per_minute=12,
                burst=3,
            )
        )

    assert (
        "internal redis detail"
        not in str(
            exc_info.value
        )
    )