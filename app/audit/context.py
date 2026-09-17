from contextvars import (
    ContextVar,
    Token,
)


_request_id: ContextVar[
    str | None
] = ContextVar(
    "audit_request_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(
    request_id: str,
) -> Token:
    normalized = request_id.strip()

    if not normalized:
        raise ValueError(
            "request_id must not be empty."
        )

    return _request_id.set(
        normalized
    )


def reset_request_id(
    token: Token,
) -> None:
    _request_id.reset(
        token
    )
