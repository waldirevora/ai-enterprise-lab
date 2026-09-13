from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings


@dataclass(frozen=True)
class DeepSeekCostEstimate:
    pricing_tier: str
    estimated_cost_usd: float


def is_deepseek_peak_time(
    now: datetime | None = None,
) -> bool:
    current = now or datetime.now(timezone.utc)

    if current.weekday() >= 5:
        return False

    hour = current.hour

    return (
        1 <= hour < 4
        or 6 <= hour < 10
    )


def estimate_deepseek_cost(
    *,
    prompt_tokens: int,
    cache_hit_tokens: int,
    cache_miss_tokens: int,
    completion_tokens: int,
    now: datetime | None = None,
) -> DeepSeekCostEstimate:
    if (
        cache_hit_tokens == 0
        and cache_miss_tokens == 0
        and prompt_tokens > 0
    ):
        cache_miss_tokens = prompt_tokens

    peak = is_deepseek_peak_time(now)

    multiplier = (
        settings.deepseek_peak_multiplier
        if peak
        else 1.0
    )

    cache_hit_price = (
        settings.deepseek_price_cache_hit_offpeak_per_m
        * multiplier
    )

    cache_miss_price = (
        settings.deepseek_price_cache_miss_offpeak_per_m
        * multiplier
    )

    output_price = (
        settings.deepseek_price_output_offpeak_per_m
        * multiplier
    )

    cost = (
        cache_hit_tokens * cache_hit_price
        + cache_miss_tokens * cache_miss_price
        + completion_tokens * output_price
    ) / 1_000_000

    return DeepSeekCostEstimate(
        pricing_tier="peak" if peak else "off_peak",
        estimated_cost_usd=round(cost, 8),
    )