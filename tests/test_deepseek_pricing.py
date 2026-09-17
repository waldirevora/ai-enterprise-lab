from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.providers.deepseek_pricing import (
    estimate_deepseek_cost,
    is_deepseek_peak_time,
)


def test_weekday_peak_time():
    now = datetime(
        2026,
        9,
        14,
        1,
        30,
        tzinfo=timezone.utc,
    )

    assert is_deepseek_peak_time(now) is True


def test_weekday_off_peak_time():
    now = datetime(
        2026,
        9,
        14,
        4,
        30,
        tzinfo=timezone.utc,
    )

    assert is_deepseek_peak_time(now) is False


def test_weekend_is_off_peak():
    now = datetime(
        2026,
        9,
        12,
        2,
        0,
        tzinfo=timezone.utc,
    )

    assert is_deepseek_peak_time(now) is False


def test_estimates_off_peak_cost(monkeypatch):
    monkeypatch.setattr(
        settings,
        "deepseek_price_cache_hit_offpeak_per_m",
        0.003,
    )
    monkeypatch.setattr(
        settings,
        "deepseek_price_cache_miss_offpeak_per_m",
        0.15,
    )
    monkeypatch.setattr(
        settings,
        "deepseek_price_output_offpeak_per_m",
        0.60,
    )

    now = datetime(
        2026,
        9,
        12,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = estimate_deepseek_cost(
        prompt_tokens=91,
        cache_hit_tokens=0,
        cache_miss_tokens=91,
        completion_tokens=40,
        now=now,
    )

    assert result.pricing_tier == "off_peak"
    assert result.estimated_cost_usd == pytest.approx(
        0.00003765
    )


def test_uses_prompt_tokens_as_cache_miss_fallback():
    now = datetime(
        2026,
        9,
        12,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = estimate_deepseek_cost(
        prompt_tokens=91,
        cache_hit_tokens=0,
        cache_miss_tokens=0,
        completion_tokens=40,
        now=now,
    )

    assert result.estimated_cost_usd == pytest.approx(
        0.00003765
    )


def test_peak_cost_uses_multiplier(monkeypatch):
    monkeypatch.setattr(
        settings,
        "deepseek_peak_multiplier",
        2.0,
    )

    now = datetime(
        2026,
        9,
        14,
        1,
        30,
        tzinfo=timezone.utc,
    )

    result = estimate_deepseek_cost(
        prompt_tokens=91,
        cache_hit_tokens=0,
        cache_miss_tokens=91,
        completion_tokens=40,
        now=now,
    )

    assert result.pricing_tier == "peak"
    assert result.estimated_cost_usd == pytest.approx(
        0.00007530
    )
