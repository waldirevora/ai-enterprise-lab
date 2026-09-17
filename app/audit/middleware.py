from uuid import uuid4

from app.audit.context import (
    reset_request_id,
    set_request_id,
)


class AuditRequestContextMiddleware:
    def __init__(
        self,
        app,
    ) -> None:
        self.app = app

    async def __call__(
        self,
        scope,
        receive,
        send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )

            return

        request_id = uuid4().hex

        state = scope.setdefault(
            "state",
            {},
        )

        state["request_id"] = (
            request_id
        )

        token = set_request_id(
            request_id
        )

        async def send_with_request_id(
            message,
        ):
            if (
                message["type"]
                == "http.response.start"
            ):
                headers = [
                    header
                    for header
                    in message.get(
                        "headers",
                        [],
                    )
                    if header[0].lower()
                    != b"x-request-id"
                ]

                headers.append(
                    (
                        b"x-request-id",
                        request_id.encode(
                            "ascii"
                        ),
                    )
                )

                message = {
                    **message,
                    "headers": headers,
                }

            await send(
                message
            )

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )

        finally:
            reset_request_id(
                token
            )
