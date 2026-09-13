from dataclasses import dataclass

from app.core.config import ProviderName, settings
from app.schemas import DataClassification


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def evaluate_provider_policy(
    *,
    provider: ProviderName,
    data_classification: DataClassification,
    external_approved: bool,
) -> PolicyDecision:
    if provider in {"local_fast", "local_deep"}:
        return PolicyDecision(
            allowed=True,
            reason="Local provider allowed.",
        )

    if provider != "external_deep":
        return PolicyDecision(
            allowed=False,
            reason="Unknown provider.",
        )

    if not settings.external_ai_enabled:
        return PolicyDecision(
            allowed=False,
            reason="External AI is globally disabled.",
        )

    if data_classification != "public":
        return PolicyDecision(
            allowed=False,
            reason=(
                "External providers are not allowed for "
                f"'{data_classification}' data."
            ),
        )

    if not external_approved:
        return PolicyDecision(
            allowed=False,
            reason=(
                "External provider requires explicit approval "
                "for this request."
            ),
        )

    return PolicyDecision(
        allowed=True,
        reason="External provider explicitly authorized.",
    )