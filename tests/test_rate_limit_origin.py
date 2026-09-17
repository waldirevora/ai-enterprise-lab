import pytest
from starlette.requests import Request

from app.rate_limit.origin import (
    RateLimitOriginError,
    build_origin_key,
    get_request_origin,
)


def make_request(
    *,
    host: str | None,
    headers: list[
        tuple[bytes, bytes]
    ] | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": (
            headers
            if headers is not None
            else []
        ),
        "client": (
            (host, 12345)
            if host is not None
            else None
        ),
        "server": (
            "testserver",
            80,
        ),
        "scheme": "http",
        "query_string": b"",
    }

    return Request(
        scope
    )


def test_request_origin_uses_client_host():
    request = make_request(
        host="203.0.113.10",
    )

    assert (
        get_request_origin(
            request
        )
        == "203.0.113.10"
    )


def test_x_forwarded_for_is_ignored():
    request = make_request(
        host="203.0.113.10",
        headers=[
            (
                b"x-forwarded-for",
                b"198.51.100.77",
            )
        ],
    )

    assert (
        get_request_origin(
            request
        )
        == "203.0.113.10"
    )


def test_origin_key_is_hashed_and_stable():
    first_request = make_request(
        host="203.0.113.10",
    )

    second_request = make_request(
        host="203.0.113.10",
    )

    first = build_origin_key(
        namespace="public-generate",
        request=first_request,
    )

    second = build_origin_key(
        namespace="public-generate",
        request=second_request,
    )

    assert first == second

    assert (
        first.startswith(
            "rate-limit:public-generate:"
        )
    )

    assert (
        "203.0.113.10"
        not in first
    )


def test_missing_request_origin_is_rejected():
    request = make_request(
        host=None,
    )

    with pytest.raises(
        RateLimitOriginError,
        match=(
            "Request origin is unavailable"
        ),
    ):
        get_request_origin(
            request
        )


def test_empty_namespace_is_rejected():
    request = make_request(
        host="203.0.113.10",
    )

    with pytest.raises(
        RateLimitOriginError,
        match=(
            "Rate limit namespace "
            "must not be empty"
        ),
    ):
        build_origin_key(
            namespace="   ",
            request=request,
        )