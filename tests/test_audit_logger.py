import json

from app.audit import logger
from app.audit.context import (
    reset_request_id,
    set_request_id,
)
from app.audit.models import (
    create_audit_event,
)


def test_audit_event_uses_request_context():
    token = set_request_id(
        "req-abc"
    )

    try:
        event = create_audit_event(
            event_type="auth.success",
            outcome="success",
            route=(
                "/v1/rag/"
                "generate-authenticated"
            ),
            method="post",
            organization_id=42,
            principal_id=10,
            reason_code=(
                "credential_valid"
            ),
        )

    finally:
        reset_request_id(
            token
        )

    assert (
        event.request_id
        == "req-abc"
    )

    assert (
        event.method
        == "POST"
    )

    assert (
        event.event_type
        == "auth.success"
    )

    assert event.event_id

    assert (
        event.timestamp.endswith(
            "Z"
        )
    )


def test_serialized_event_does_not_include_sensitive_metadata():
    event = create_audit_event(
        event_type="auth.failure",
        outcome="failure",
        reason_code=(
            "credential_invalid"
        ),
        metadata={
            "status_code": 401,
            "Authorization": (
                "Bearer VERY_SECRET"
            ),
            "prompt": (
                "PRIVATE_PROMPT"
            ),
        },
    )

    serialized = (
        logger.serialize_audit_event(
            event
        )
    )

    body = json.loads(
        serialized
    )

    assert body["metadata"] == {
        "status_code": 401,
    }

    assert (
        "VERY_SECRET"
        not in serialized
    )

    assert (
        "PRIVATE_PROMPT"
        not in serialized
    )


def test_logging_failure_does_not_break_caller(
    monkeypatch,
):
    def broken_logger(
        message,
    ):
        raise RuntimeError(
            "sink failed"
        )

    monkeypatch.setattr(
        logger.audit_logger,
        "info",
        broken_logger,
    )

    event = logger.emit_audit_event(
        event_type=(
            "rate_limit.unavailable"
        ),
        outcome="unavailable",
        reason_code=(
            "redis_unavailable"
        ),
    )

    assert (
        event.event_type
        == "rate_limit.unavailable"
    )
