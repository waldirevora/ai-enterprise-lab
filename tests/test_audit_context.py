import pytest

from app.audit.context import (
    get_request_id,
    reset_request_id,
    set_request_id,
)


def test_request_id_defaults_to_none():
    assert get_request_id() is None


def test_request_id_can_be_set_and_reset():
    token = set_request_id(
        "request-123"
    )

    try:
        assert (
            get_request_id()
            == "request-123"
        )

    finally:
        reset_request_id(
            token
        )

    assert get_request_id() is None


def test_empty_request_id_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "request_id must not be empty"
        ),
    ):
        set_request_id(
            "   "
        )
