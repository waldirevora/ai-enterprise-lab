import asyncio

import pytest
from fastapi import HTTPException

from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.rate_limit import http
from app.rate_limit.limiter import (
    RateLimitUnavailableError,
)
from app.rate_limit.models import (
    RateLimitDecision,
)


def _metric_value(
    name: str,
    labels: dict[str, str],
) -> float:
    value = METRICS_REGISTRY.get_sample_value(
        name,
        labels,
    )

    return float(
        value or 0.0
    )


def test_rate_limited_request_records_metric(
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

    labels = {
        "outcome": "rate_limited",
    }

    before = _metric_value(
        "ai_enterprise_rate_limit_events_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            http.enforce_rate_limit(
                key="metrics:test",
                rate_per_minute=30,
                burst=5,
            )
        )

    assert exc_info.value.status_code == 429

    assert _metric_value(
        "ai_enterprise_rate_limit_events_total",
        labels,
    ) == before + 1


def test_rate_limit_unavailable_records_metric(
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

    labels = {
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_rate_limit_events_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            http.enforce_rate_limit(
                key="metrics:test",
                rate_per_minute=30,
                burst=5,
            )
        )

    assert exc_info.value.status_code == 503

    assert _metric_value(
        "ai_enterprise_rate_limit_events_total",
        labels,
    ) == before + 1


def test_allowed_request_does_not_record_error_metric(
    monkeypatch,
):
    async def fake_consume_token(
        **kwargs,
    ):
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

    denied_before = _metric_value(
        "ai_enterprise_rate_limit_events_total",
        {
            "outcome": "rate_limited",
        },
    )

    unavailable_before = _metric_value(
        "ai_enterprise_rate_limit_events_total",
        {
            "outcome": "unavailable",
        },
    )

    result = asyncio.run(
        http.enforce_rate_limit(
            key="metrics:test",
            rate_per_minute=30,
            burst=5,
        )
    )

    assert result.allowed is True

    assert _metric_value(
        "ai_enterprise_rate_limit_events_total",
        {
            "outcome": "rate_limited",
        },
    ) == denied_before

    assert _metric_value(
        "ai_enterprise_rate_limit_events_total",
        {
            "outcome": "unavailable",
        },
    ) == unavailable_before
