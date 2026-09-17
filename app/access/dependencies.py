from typing import Annotated

from fastapi import (
    Header,
    HTTPException,
    Request,
    status,
)

from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
    authenticate_api_key,
)
from app.access.context import PrincipalContext
from app.core.config import settings
from app.rate_limit.http import (
    enforce_rate_limit,
)
from app.rate_limit.origin import (
    RateLimitOriginError,
    build_origin_key,
)


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


async def require_rate_limited_principal_context(
    request: Request,
    authorization: Annotated[
        str | None,
        Header(
            alias="Authorization",
        ),
    ] = None,
) -> PrincipalContext:
    #
    # 1. PRE-AUTH.
    #
    # Acontece antes de parsing completo da
    # credencial e antes de PostgreSQL.
    #
    # Isso limita brute force, credential
    # stuffing e credenciais aleatórias.
    #
    try:
        preauth_key = build_origin_key(
            namespace="auth-preauth",
            request=request,
        )

    except RateLimitOriginError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Rate limit service unavailable."
            ),
        ) from exc

    await enforce_rate_limit(
        key=preauth_key,
        rate_per_minute=(
            settings
            .rate_limit_auth_preauth_per_minute
        ),
        burst=(
            settings
            .rate_limit_auth_preauth_burst
        ),
    )

    #
    # 2. Autenticação original.
    #
    # Mantemos require_principal_context()
    # isolado para preservar o contrato de
    # autenticação já existente.
    #
    context = await require_principal_context(
        authorization=authorization
    )

    #
    # 3. POST-AUTH.
    #
    # A chave usa somente IDs internos.
    #
    # Nenhuma API key, token ou outro segredo
    # é armazenado no Redis.
    #
    principal_key = (
        "rate-limit:principal:"
        f"{context.organization_id}:"
        f"{context.principal_id}"
    )

    await enforce_rate_limit(
        key=principal_key,
        rate_per_minute=(
            settings
            .rate_limit_auth_principal_per_minute
        ),
        burst=(
            settings
            .rate_limit_auth_principal_burst
        ),
    )

    return context