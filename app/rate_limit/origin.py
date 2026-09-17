import hashlib

from fastapi import Request


class RateLimitOriginError(Exception):
    pass


def get_request_origin(
    request: Request,
) -> str:
    client = request.client

    if (
        client is None
        or not client.host
    ):
        raise RateLimitOriginError(
            "Request origin is unavailable."
        )

    return client.host


def build_origin_key(
    *,
    namespace: str,
    request: Request,
) -> str:
    normalized_namespace = (
        namespace.strip()
    )

    if not normalized_namespace:
        raise RateLimitOriginError(
            "Rate limit namespace must not be empty."
        )

    origin = get_request_origin(
        request
    )

    digest = hashlib.sha256(
        origin.encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        "rate-limit:"
        f"{normalized_namespace}:"
        f"{digest}"
    )