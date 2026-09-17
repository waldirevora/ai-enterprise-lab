import re
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Any,
    Literal,
    Mapping,
)
from uuid import uuid4

from app.audit.context import (
    get_request_id,
)
from app.audit.sanitizer import (
    sanitize_metadata,
)


AuditOutcome = Literal[
    "success",
    "failure",
    "allowed",
    "denied",
    "unavailable",
]


_MACHINE_CODE_PATTERN = re.compile(
    r"^[a-z0-9_.-]{1,100}$"
)


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    event_id: str
    request_id: str | None

    event_type: str
    outcome: AuditOutcome

    route: str | None = None
    method: str | None = None

    organization_id: int | None = None
    principal_id: int | None = None

    provider: str | None = None
    classification: str | None = None

    reason_code: str | None = None

    metadata: dict[
        str,
        str
        | int
        | float
        | bool
        | None,
    ] | None = None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "request_id": self.request_id,
            "event_type": self.event_type,
            "outcome": self.outcome,
            "route": self.route,
            "method": self.method,
            "organization_id": (
                self.organization_id
            ),
            "principal_id": (
                self.principal_id
            ),
            "provider": self.provider,
            "classification": (
                self.classification
            ),
            "reason_code": (
                self.reason_code
            ),
            "metadata": (
                self.metadata
                if self.metadata
                is not None
                else {}
            ),
        }


def _validate_machine_code(
    *,
    value: str,
    field_name: str,
) -> str:
    normalized = value.strip()

    if not _MACHINE_CODE_PATTERN.fullmatch(
        normalized
    ):
        raise ValueError(
            f"{field_name} must be a "
            "machine-safe identifier."
        )

    return normalized


def _utc_timestamp(
    value: datetime | None = None,
) -> str:
    timestamp = (
        value
        if value is not None
        else datetime.now(
            timezone.utc
        )
    )

    if timestamp.tzinfo is None:
        raise ValueError(
            "Audit timestamp must be "
            "timezone-aware."
        )

    return (
        timestamp
        .astimezone(
            timezone.utc
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def create_audit_event(
    *,
    event_type: str,
    outcome: AuditOutcome,
    route: str | None = None,
    method: str | None = None,
    organization_id: int | None = None,
    principal_id: int | None = None,
    provider: str | None = None,
    classification: str | None = None,
    reason_code: str | None = None,
    metadata: Mapping[
        str,
        Any,
    ]
    | None = None,
    request_id: str | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
) -> AuditEvent:
    normalized_event_type = (
        _validate_machine_code(
            value=event_type,
            field_name="event_type",
        )
    )

    normalized_reason_code = None

    if reason_code is not None:
        normalized_reason_code = (
            _validate_machine_code(
                value=reason_code,
                field_name="reason_code",
            )
        )

    resolved_request_id = (
        request_id
        if request_id is not None
        else get_request_id()
    )

    return AuditEvent(
        timestamp=_utc_timestamp(
            timestamp
        ),
        event_id=(
            event_id
            if event_id is not None
            else uuid4().hex
        ),
        request_id=(
            resolved_request_id
        ),
        event_type=(
            normalized_event_type
        ),
        outcome=outcome,
        route=(
            route.strip()
            if route
            else None
        ),
        method=(
            method.strip().upper()
            if method
            else None
        ),
        organization_id=(
            organization_id
        ),
        principal_id=principal_id,
        provider=provider,
        classification=(
            classification
        ),
        reason_code=(
            normalized_reason_code
        ),
        metadata=sanitize_metadata(
            metadata
        ),
    )
