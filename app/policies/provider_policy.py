from dataclasses import dataclass

from app.core.config import (
    ProviderName,
    settings,
)
from app.schemas import DataClassification


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    reason_code: str


def evaluate_provider_policy(
    *,
    provider: ProviderName,
    data_classification: DataClassification,
    external_approved: bool,
) -> PolicyDecision:
    if provider in {
        "local_fast",
        "local_deep",
    }:
        return PolicyDecision(
            allowed=True,
            reason="Local provider allowed.",
            reason_code=(
                "local_provider_allowed"
            ),
        )

    if provider != "external_deep":
        return PolicyDecision(
            allowed=False,
            reason="Unknown provider.",
            reason_code=(
                "unknown_provider"
            ),
        )

    if not settings.external_ai_enabled:
        return PolicyDecision(
            allowed=False,
            reason=(
                "External AI is globally disabled."
            ),
            reason_code=(
                "external_ai_globally_disabled"
            ),
        )

    if data_classification != "public":
        return PolicyDecision(
            allowed=False,
            reason=(
                "External providers are not allowed for "
                f"'{data_classification}' data."
            ),
            reason_code=(
                "external_provider_non_public_data"
            ),
        )

    if not external_approved:
        return PolicyDecision(
            allowed=False,
            reason=(
                "External provider requires explicit approval "
                "for this request."
            ),
            reason_code=(
                "external_provider_approval_required"
            ),
        )

    return PolicyDecision(
        allowed=True,
        reason=(
            "External provider explicitly authorized."
        ),
        reason_code=(
            "external_provider_authorized"
        ),
    )
