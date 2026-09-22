import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_agent_timeout_defaults():
    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.agent_tool_timeout_seconds
        == 20.0
    )

    assert (
        settings.agent_generation_timeout_seconds
        == 30.0
    )


def test_agent_timeout_custom_values():
    settings = Settings(
        _env_file=None,
        agent_tool_timeout_seconds=15.0,
        agent_generation_timeout_seconds=60.0,
    )

    assert (
        settings.agent_tool_timeout_seconds
        == 15.0
    )

    assert (
        settings.agent_generation_timeout_seconds
        == 60.0
    )


def test_agent_timeout_env_values(
    monkeypatch,
):
    monkeypatch.setenv(
        "AGENT_TOOL_TIMEOUT_SECONDS",
        "25.0",
    )

    monkeypatch.setenv(
        "AGENT_GENERATION_TIMEOUT_SECONDS",
        "45.0",
    )

    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.agent_tool_timeout_seconds
        == 25.0
    )

    assert (
        settings.agent_generation_timeout_seconds
        == 45.0
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "agent_tool_timeout_seconds",
            0.0,
        ),
        (
            "agent_tool_timeout_seconds",
            121.0,
        ),
        (
            "agent_generation_timeout_seconds",
            0.0,
        ),
        (
            "agent_generation_timeout_seconds",
            181.0,
        ),
    ],
)
def test_agent_timeout_rejects_invalid_values(
    field,
    value,
):
    with pytest.raises(
        ValidationError
    ):
        Settings(
            _env_file=None,
            **{
                field: value,
            },
        )
