from time import perf_counter

from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.observability.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    http_status_class,
)


UNMATCHED_ROUTE_LABEL = "__unmatched__"
UNKNOWN_HTTP_METHOD_LABEL = "OTHER"

ALLOWED_HTTP_METHODS = frozenset(
    {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
        "TRACE",
        "CONNECT",
    }
)


def http_method_label(
    method: object,
) -> str:
    normalized = str(
        method or ""
    ).upper()

    if normalized in ALLOWED_HTTP_METHODS:
        return normalized

    return UNKNOWN_HTTP_METHOD_LABEL


def _route_label(
    scope: Scope,
) -> str:
    route = scope.get("route")

    path = getattr(
        route,
        "path",
        None,
    )

    if not path:
        return UNMATCHED_ROUTE_LABEL

    return str(path)


class HttpMetricsMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        started_at = perf_counter()

        status_code = 500

        async def send_with_status(
            message: Message,
        ) -> None:
            nonlocal status_code

            if (
                message["type"]
                == "http.response.start"
            ):
                status_code = int(
                    message["status"]
                )

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_status,
            )

        finally:
            duration_seconds = (
                perf_counter()
                - started_at
            )

            method = http_method_label(
                scope.get(
                    "method"
                )
            )

            route = _route_label(
                scope
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                route=route,
                status_class=(
                    http_status_class(
                        status_code
                    )
                ),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                route=route,
            ).observe(
                duration_seconds
            )
