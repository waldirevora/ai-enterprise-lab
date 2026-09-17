import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _production_settings(
    **overrides,
) -> Settings:
    values = {
        "app_env": "production",
        "allowed_hosts": (
            "api.example.com",
        ),
        "postgres_password": (
            "test-postgres-password"
        ),
        "redis_password": (
            "test-redis-password"
        ),
    }

    values.update(overrides)

    return Settings(
        _env_file=None,
        **values,
    )


def test_secure_production_configuration_is_accepted():
    settings = _production_settings()

    assert (
        settings.app_env
        == "production"
    )


def test_production_requires_postgres_password():
    with pytest.raises(
        ValidationError,
        match=(
            "POSTGRES_PASSWORD is required "
            "in production"
        ),
    ):
        _production_settings(
            postgres_password="",
        )


def test_production_rate_limit_requires_redis_password():
    with pytest.raises(
        ValidationError,
        match=(
            "REDIS_PASSWORD is required "
            "in production"
        ),
    ):
        _production_settings(
            redis_password="",
        )


def test_production_requires_rate_limiting():
    with pytest.raises(
        ValidationError,
        match=(
            "RATE_LIMIT_ENABLED must be true "
            "in production"
        ),
    ):
        _production_settings(
            rate_limit_enabled=False,
        )

def test_external_ai_requires_api_key():
    with pytest.raises(
        ValidationError,
        match=(
            "DEEPSEEK_API_KEY is required "
            "when external AI is enabled"
        ),
    ):
        Settings(
            external_ai_enabled=True,
            deepseek_api_key="",
            _env_file=None,
        )


def test_production_rejects_allowed_host_wildcard():
    with pytest.raises(
        ValidationError,
        match=(
            "Production ALLOWED_HOSTS "
            "must not contain wildcards"
        ),
    ):
        _production_settings(
            allowed_hosts=("*",),
        )


def test_production_requires_explicit_deployment_host():
    with pytest.raises(
        ValidationError,
        match=(
            "Production ALLOWED_HOSTS must "
            "include an explicit deployment host"
        ),
    ):
        _production_settings(
            allowed_hosts=(
                "localhost",
                "127.0.0.1",
                "testserver",
            ),
        )
