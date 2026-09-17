from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


client = TestClient(app)


def test_default_allowed_hosts_are_restrictive():
    settings = Settings(
        _env_file=None,
    )

    assert "*" not in settings.allowed_hosts

    assert (
        "localhost"
        in settings.allowed_hosts
    )

    assert (
        "127.0.0.1"
        in settings.allowed_hosts
    )

    assert (
        "testserver"
        in settings.allowed_hosts
    )


def test_trusted_host_is_accepted():
    response = client.get(
        "/health",
        headers={
            "host": "testserver",
        },
    )

    assert response.status_code == 200


def test_untrusted_host_is_rejected():
    response = client.get(
        "/health",
        headers={
            "host": "evil.example",
        },
    )

    assert response.status_code == 400
