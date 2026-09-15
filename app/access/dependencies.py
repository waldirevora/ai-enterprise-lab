from typing import Annotated

from fastapi import (
    Header,
    HTTPException,
    status,
)

from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
    authenticate_api_key,
)
from app.access.context import PrincipalContext


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API credential.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def _extract_bearer_token(
    authorization: str | None,
) -> str:
    if authorization is None:
        raise _unauthorized_exception()

    parts = authorization.split()

    if len(parts) != 2:
        raise _unauthorized_exception()

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise _unauthorized_exception()

    if not token:
        raise _unauthorized_exception()

    return token


async def require_principal_context(
    authorization: Annotated[
        str | None,
        Header(
            alias="Authorization",
        ),
    ] = None,
) -> PrincipalContext:
    token = _extract_bearer_token(
        authorization
    )

    try:
        return await authenticate_api_key(
            token
        )

    except AuthenticationError as exc:
        raise _unauthorized_exception() from exc

    except AuthenticationUnavailableError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Authentication service unavailable."
            ),
        ) from exc