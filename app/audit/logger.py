import json
import logging
import sys
from typing import Any, Mapping

from app.audit.models import (
    AuditEvent,
    AuditOutcome,
    create_audit_event,
)


AUDIT_LOGGER_NAME = (
    "ai_enterprise_lab.audit"
)


audit_logger = logging.getLogger(
    AUDIT_LOGGER_NAME
)


if not audit_logger.handlers:
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        logging.Formatter(
            "%(message)s"
        )
    )

    audit_logger.addHandler(
        handler
    )


audit_logger.setLevel(
    logging.INFO
)

audit_logger.propagate = False


def serialize_audit_event(
    event: AuditEvent,
) -> str:
    return json.dumps(
        event.to_dict(),
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
        sort_keys=True,
    )


def emit_audit_event(
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
) -> AuditEvent:
    event = create_audit_event(
        event_type=event_type,
        outcome=outcome,
        route=route,
        method=method,
        organization_id=(
            organization_id
        ),
        principal_id=principal_id,
        provider=provider,
        classification=(
            classification
        ),
        reason_code=reason_code,
        metadata=metadata,
    )

    serialized = serialize_audit_event(
        event
    )

    try:
        audit_logger.info(
            serialized
        )

    except Exception:
        #
        # Foundation observacional:
        # falha do sink de auditoria não
        # altera a decisão de segurança
        # ou a resposta HTTP.
        #
        pass

    return event
