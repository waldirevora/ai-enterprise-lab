import asyncio

from fastapi.testclient import TestClient

import app.health.readiness as readiness
import app.main as main_module
from app.rate_limit.backend import (
    RateLimitBackendError,
    RedisRateLimitBackend,
)


client = TestClient(
    main_module.app
)


def test_health_remains_simple_liveness(
    monkeypatch,
):
    async def should_not_run():
        raise AssertionError(
            "Readiness must not affect /health."
        )

    monkeypatch.setattr(
        main_module,
        "check_readiness",
        should_not_run,
    )

    response = client.get(
        "/health"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_ready_endpoint_returns_200_when_ready(
    monkeypatch,
):
    async def ready():
        return True

    monkeypatch.setattr(
        main_module,
        "check_readiness",
        ready,
    )

    response = client.get(
        "/ready"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }


def test_ready_endpoint_returns_sanitized_503(
    monkeypatch,
):
    async def unavailable():
        raise readiness.ReadinessCheckError(
            "postgres.internal:5432 secret detail"
        )

    monkeypatch.setattr(
        main_module,
        "check_readiness",
        unavailable,
    )

    response = client.get(
        "/ready"
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }

    payload = response.text

    assert "postgres.internal" not in payload
    assert "5432" not in payload
    assert "secret detail" not in payload


def test_readiness_skips_redis_when_rate_limit_disabled(
    monkeypatch,
):
    async def database_ok():
        return True

    async def redis_must_not_run():
        raise AssertionError(
            "Redis must be skipped."
        )

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_ok,
    )

    monkeypatch.setattr(
        readiness.backend,
        "check_connection",
        redis_must_not_run,
    )

    monkeypatch.setattr(
        readiness.settings,
        "rate_limit_enabled",
        False,
    )

    assert asyncio.run(
        readiness.check_readiness()
    ) is True


def test_postgres_failure_makes_readiness_fail(
    monkeypatch,
):
    async def database_failure():
        raise readiness.DatabaseConnectionError(
            "internal postgres detail"
        )

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_failure,
    )

    try:
        asyncio.run(
            readiness.check_readiness()
        )

    except readiness.ReadinessCheckError as exc:
        assert str(exc) == (
            "Required dependency unavailable."
        )

    else:
        raise AssertionError(
            "Readiness should have failed."
        )


def test_redis_failure_makes_readiness_fail(
    monkeypatch,
):
    async def database_ok():
        return True

    async def redis_failure():
        raise RateLimitBackendError(
            "internal redis detail"
        )

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_ok,
    )

    monkeypatch.setattr(
        readiness.backend,
        "check_connection",
        redis_failure,
    )

    monkeypatch.setattr(
        readiness.settings,
        "rate_limit_enabled",
        True,
    )

    try:
        asyncio.run(
            readiness.check_readiness()
        )

    except readiness.ReadinessCheckError as exc:
        assert str(exc) == (
            "Required dependency unavailable."
        )

    else:
        raise AssertionError(
            "Readiness should have failed."
        )


def test_redis_backend_check_connection_returns_true():
    class FakeRedis:
        async def ping(self):
            return True

    backend = RedisRateLimitBackend(
        client=FakeRedis()
    )

    assert asyncio.run(
        backend.check_connection()
    ) is True


def test_redis_backend_check_connection_sanitizes_failure():
    class FakeRedis:
        async def ping(self):
            raise OSError(
                "redis.internal:6379 private detail"
            )

    backend = RedisRateLimitBackend(
        client=FakeRedis()
    )

    try:
        asyncio.run(
            backend.check_connection()
        )

    except RateLimitBackendError as exc:
        assert str(exc) == (
            "Rate limit backend unavailable."
        )

        assert "redis.internal" not in str(exc)
        assert "6379" not in str(exc)

    else:
        raise AssertionError(
            "Redis connection check should fail."
        )

def test_postgres_false_makes_readiness_fail(
    monkeypatch,
):
    async def database_not_ready():
        return False

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_not_ready,
    )

    try:
        asyncio.run(
            readiness.check_readiness()
        )

    except readiness.ReadinessCheckError as exc:
        assert str(exc) == (
            "Required dependency unavailable."
        )

    else:
        raise AssertionError(
            "Readiness should have failed."
        )


def test_redis_false_makes_readiness_fail(
    monkeypatch,
):
    async def database_ok():
        return True

    async def redis_not_ready():
        return False

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_ok,
    )

    monkeypatch.setattr(
        readiness.backend,
        "check_connection",
        redis_not_ready,
    )

    monkeypatch.setattr(
        readiness.settings,
        "rate_limit_enabled",
        True,
    )

    try:
        asyncio.run(
            readiness.check_readiness()
        )

    except readiness.ReadinessCheckError as exc:
        assert str(exc) == (
            "Required dependency unavailable."
        )

    else:
        raise AssertionError(
            "Readiness should have failed."
        )


def test_redis_backend_false_ping_is_rejected():
    class FakeRedis:
        async def ping(self):
            return False

    backend = RedisRateLimitBackend(
        client=FakeRedis()
    )

    try:
        asyncio.run(
            backend.check_connection()
        )

    except RateLimitBackendError as exc:
        assert str(exc) == (
            "Invalid rate limit backend response."
        )

    else:
        raise AssertionError(
            "Redis false ping should fail."
        )


def test_default_redis_backend_disables_automatic_retries():
    backend = RedisRateLimitBackend()

    retry = (
        backend
        ._client
        .connection_pool
        .connection_kwargs
        .get("retry")
    )

    assert retry is not None
    assert retry._retries == 0


def test_redis_readiness_timeout_is_sanitized(
    monkeypatch,
):
    async def database_ok():
        return True

    async def redis_hangs():
        await asyncio.sleep(
            60
        )

        return True

    monkeypatch.setattr(
        readiness,
        "check_database_connection",
        database_ok,
    )

    monkeypatch.setattr(
        readiness.backend,
        "check_connection",
        redis_hangs,
    )

    monkeypatch.setattr(
        readiness.settings,
        "rate_limit_enabled",
        True,
    )

    monkeypatch.setattr(
        readiness.settings,
        "redis_readiness_timeout_seconds",
        0.01,
    )

    try:
        asyncio.run(
            readiness.check_readiness()
        )

    except readiness.ReadinessCheckError as exc:
        assert str(exc) == (
            "Required dependency unavailable."
        )

    else:
        raise AssertionError(
            "Readiness should have timed out."
        )
