from app.audit.sanitizer import (
    sanitize_metadata,
)


def test_safe_metadata_is_preserved():
    result = sanitize_metadata(
        {
            "status_code": 429,
            "retry_after_seconds": 60,
            "unit_id": 12,
            "unit_slug": "financeiro",
        }
    )

    assert result == {
        "status_code": 429,
        "retry_after_seconds": 60,
        "unit_id": 12,
        "unit_slug": "financeiro",
    }


def test_sensitive_and_unknown_metadata_is_dropped():
    result = sanitize_metadata(
        {
            "status_code": 401,
            "Authorization": (
                "Bearer SECRET"
            ),
            "api_key": "SECRET",
            "token": "SECRET",
            "password": "SECRET",
            "prompt": "private prompt",
            "question": "private question",
            "content": "private content",
            "reasoning_content": (
                "private reasoning"
            ),
            "custom_note": (
                "should not be accepted"
            ),
        }
    )

    assert result == {
        "status_code": 401,
    }


def test_nested_metadata_is_rejected():
    result = sanitize_metadata(
        {
            "status_code": {
                "nested": "value"
            },
            "retrieved_chunks": [
                1,
                2,
            ],
        }
    )

    assert result == {}


def test_string_metadata_is_normalized_and_limited():
    result = sanitize_metadata(
        {
            "model": (
                "model-name\n"
                + ("x" * 300)
            )
        }
    )

    value = result["model"]

    assert "\n" not in value
    assert len(value) <= 160
