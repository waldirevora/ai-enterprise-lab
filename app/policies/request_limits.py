from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class RequestLimits:
    max_output_tokens: int


def validate_request_limits(
    *,
    prompt: str,
    requested_max_output_tokens: int | None,
) -> RequestLimits:
    if len(prompt) > settings.ai_max_prompt_chars:
        raise ValueError(
            f"Prompt exceeds the limit of "
            f"{settings.ai_max_prompt_chars} characters."
        )

    max_output_tokens = (
        requested_max_output_tokens
        if requested_max_output_tokens is not None
        else settings.ai_max_output_tokens
    )

    if max_output_tokens > settings.ai_max_output_tokens:
        raise ValueError(
            f"Output token limit cannot exceed "
            f"{settings.ai_max_output_tokens}."
        )

    return RequestLimits(
        max_output_tokens=max_output_tokens,
    )