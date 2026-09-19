from app.audit.sanitizer import (
    sanitize_metadata,
)


def test_privacy_sensitive_audit_metadata_is_discarded():
    sensitive_values = {
        "prompt": "PRIVATE_PROMPT",
        "question": "PRIVATE_QUESTION",
        "response": "PRIVATE_RESPONSE",
        "content": "PRIVATE_DOCUMENT_CONTENT",
        "source_uri": (
            "https://internal.example/"
            "?token=PRIVATE_TOKEN"
        ),
        "authorization": "Bearer PRIVATE_TOKEN",
        "api_key": "PRIVATE_API_KEY",
        "password": "PRIVATE_PASSWORD",
        "secret": "PRIVATE_SECRET",
        "reasoning_content": (
            "PRIVATE_REASONING"
        ),
        "request_body": "PRIVATE_REQUEST_BODY",
        "raw_exception": (
            "PRIVATE_INTERNAL_EXCEPTION"
        ),
    }

    metadata = {
        "status_code": 403,
        **sensitive_values,
    }

    sanitized = sanitize_metadata(
        metadata
    )

    assert sanitized == {
        "status_code": 403,
    }

    serialized = repr(
        sanitized
    )

    for value in sensitive_values.values():
        assert value not in serialized
