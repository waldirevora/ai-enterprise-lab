from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Any

from starlette.datastructures import (
    MutableHeaders,
)


ASGIApp = Callable[
    [
        dict[str, Any],
        Callable[..., Awaitable[Any]],
        Callable[..., Awaitable[Any]],
    ],
    Awaitable[Any],
]


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[
            ...,
            Awaitable[Any],
        ],
        send: Callable[
            ...,
            Awaitable[Any],
        ],
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        async def send_with_headers(
            message: dict[str, Any],
        ) -> None:
            if (
                message["type"]
                == "http.response.start"
            ):
                headers = MutableHeaders(
                    scope=message
                )

                headers[
                    "X-Content-Type-Options"
                ] = "nosniff"

                headers[
                    "X-Frame-Options"
                ] = "DENY"

                headers[
                    "Referrer-Policy"
                ] = "no-referrer"

                headers[
                    "Permissions-Policy"
                ] = (
                    "camera=(), "
                    "microphone=(), "
                    "geolocation=()"
                )

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_headers,
        )
