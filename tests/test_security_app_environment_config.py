import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_app_env_defaults_to_development(
    monkeypatch,
):
    monkeypatch.delenv(
        "APP_ENV",
        raising=False,
    )

    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.app_env
        == "development"
    )


@pytest.mark.parametrize(
    "app_env",
    [
        "development",
        "test",
        "production",
    ],
)
def test_app_env_accepts_supported_values(
    app_env,
):
    kwargs = {
        "app_env": app_env,
    }

    if app_env == "production":
        kwargs.update(
            {
                "postgres_password": (
                    "test-postgres-password"
                ),
                "redis_password": (
                    "test-redis-password"
                ),
                "allowed_hosts": (
                    "api.example.com",
                ),
            }
        )

    settings = Settings(
        _env_file=None,
        **kwargs,
    )

    assert (
        settings.app_env
        == app_env
    )


def test_app_env_rejects_unknown_value():
    with pytest.raises(
        ValidationError
    ):
        Settings(
            app_env="staging",
            _env_file=None,
        )
