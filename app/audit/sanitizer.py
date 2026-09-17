from typing import Any, Mapping


SAFE_METADATA_KEYS = frozenset(
    {
        "status_code",
        "retry_after_seconds",
        "unit_id",
        "unit_slug",
        "provider_backend",
        "model",
        "retrieved_chunks",
        "prompt_tokens",
        "generated_tokens",
        "reasoning_tokens",
        "pricing_tier",
    }
)


_MAX_STRING_LENGTH = 160


def _sanitize_scalar(
    value: Any,
) -> (
    str
    | int
    | float
    | bool
    | None
):
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        normalized = " ".join(
            value.split()
        )

        if (
            len(normalized)
            > _MAX_STRING_LENGTH
        ):
            normalized = (
                normalized[
                    : _MAX_STRING_LENGTH - 3
                ]
                + "..."
            )

        return normalized

    raise TypeError(
        "Unsupported audit metadata value."
    )


def sanitize_metadata(
    metadata: Mapping[
        str,
        Any,
    ]
    | None,
) -> dict[
    str,
    str
    | int
    | float
    | bool
    | None,
]:
    if metadata is None:
        return {}

    sanitized = {}

    for key, value in metadata.items():
        if (
            not isinstance(
                key,
                str,
            )
            or key
            not in SAFE_METADATA_KEYS
        ):
            continue

        try:
            sanitized[key] = (
                _sanitize_scalar(
                    value
                )
            )

        except TypeError:
            continue

    return sanitized
