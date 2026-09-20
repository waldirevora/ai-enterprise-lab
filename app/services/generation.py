from time import perf_counter

from fastapi import HTTPException

from app.audit.logger import emit_audit_event
from app.core.config import ProviderName, settings
from app.observability.metrics import (
    ESTIMATED_EXTERNAL_COST_USD_TOTAL,
    GENERATION_DURATION_SECONDS,
    GENERATION_REQUESTS_TOTAL,
    TOKENS_TOTAL,
)
from app.policies.provider_policy import evaluate_provider_policy
from app.policies.request_limits import validate_request_limits
from app.providers.catalog import get_provider_catalog
from app.providers.deepseek import (
    DeepSeekProvider,
    DeepSeekProviderError,
)
from app.providers.deepseek_pricing import estimate_deepseek_cost
from app.providers.ollama import (
    OllamaProvider,
    OllamaProviderError,
)
from app.schemas import GenerateRequest, GenerateResponse


ollama_provider = OllamaProvider(
    settings.ollama_base_url
)

deepseek_provider = DeepSeekProvider(
    base_url=settings.deepseek_base_url,
    api_key=settings.deepseek_api_key,
    thinking_enabled=settings.deepseek_thinking_enabled,
    reasoning_effort=settings.deepseek_reasoning_effort,
)


def _record_generation_outcome(
    *,
    provider: str,
    backend: str,
    outcome: str,
) -> None:
    GENERATION_REQUESTS_TOTAL.labels(
        provider=provider,
        backend=backend,
        outcome=outcome,
    ).inc()


ALLOWED_EXTERNAL_PRICING_TIERS = frozenset(
    {
        "peak",
        "off_peak",
    }
)


def _record_generation_usage(
    *,
    response: GenerateResponse,
) -> None:
    token_values = (
        (
            "prompt",
            response.prompt_tokens,
        ),
        (
            "generated",
            response.generated_tokens,
        ),
        (
            "reasoning",
            response.reasoning_tokens,
        ),
        (
            "cache_hit",
            response.prompt_cache_hit_tokens,
        ),
        (
            "cache_miss",
            response.prompt_cache_miss_tokens,
        ),
    )

    for token_type, value in token_values:
        if value is None or value <= 0:
            continue

        TOKENS_TOTAL.labels(
            provider=response.provider,
            token_type=token_type,
        ).inc(
            value
        )

    if (
        response.backend == "deepseek"
        and response.pricing_tier
        in ALLOWED_EXTERNAL_PRICING_TIERS
        and response.estimated_cost_usd
        is not None
        and response.estimated_cost_usd > 0
    ):
        ESTIMATED_EXTERNAL_COST_USD_TOTAL.labels(
            provider=response.provider,
            pricing_tier=response.pricing_tier,
        ).inc(
            response.estimated_cost_usd
        )


def _record_generation_success(
    *,
    provider: str,
    backend: str,
    started_at: float,
) -> None:
    duration_seconds = max(
        perf_counter() - started_at,
        0.0,
    )

    GENERATION_REQUESTS_TOTAL.labels(
        provider=provider,
        backend=backend,
        outcome="success",
    ).inc()

    GENERATION_DURATION_SECONDS.labels(
        provider=provider,
        backend=backend,
    ).observe(
        duration_seconds
    )


async def generate_text(
    request: GenerateRequest,
) -> GenerateResponse:
    provider_name: ProviderName = (
        request.provider or settings.ai_default_provider
    )

    policy = evaluate_provider_policy(
        provider=provider_name,
        data_classification=request.data_classification,
        external_approved=request.external_approved,
    )

    if provider_name == "external_deep":
        if policy.allowed:
            emit_audit_event(
                event_type=(
                    "provider.external.allowed"
                ),
                outcome="allowed",
                provider=provider_name,
                classification=(
                    request.data_classification
                ),
                reason_code=(
                    policy.reason_code
                ),
            )

        else:
            emit_audit_event(
                event_type=(
                    "provider.external.blocked"
                ),
                outcome="denied",
                provider=provider_name,
                classification=(
                    request.data_classification
                ),
                reason_code=(
                    policy.reason_code
                ),
                metadata={
                    "status_code": 403,
                },
            )

    if not policy.allowed:
        _record_generation_outcome(
            provider=provider_name,
            backend="preflight",
            outcome="rejected",
        )

        raise HTTPException(
            status_code=403,
            detail=policy.reason,
        )

    try:
        limits = validate_request_limits(
            prompt=request.prompt,
            requested_max_output_tokens=request.max_output_tokens,
        )
    except ValueError as exc:
        _record_generation_outcome(
            provider=provider_name,
            backend="preflight",
            outcome="rejected",
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    catalog = get_provider_catalog()
    provider_config = catalog["providers"][provider_name]

    if provider_config["backend"] == "ollama":
        started_at = perf_counter()

        try:
            result = await ollama_provider.generate(
                model=provider_config["model"],
                prompt=request.prompt,
                temperature=request.temperature,
                num_ctx=request.num_ctx,
                max_output_tokens=limits.max_output_tokens,
            )
        except OllamaProviderError as exc:
            _record_generation_outcome(
                provider=provider_name,
                backend="ollama",
                outcome="unavailable",
            )

            raise HTTPException(
                status_code=503,
                detail=(
                    "AI provider service unavailable."
                ),
            ) from exc

        total_duration = result.get("total_duration")

        response = GenerateResponse(
            provider=provider_name,
            backend="ollama",
            model=provider_config["model"],
            response=result["response"],
            prompt_tokens=result.get("prompt_eval_count"),
            generated_tokens=result.get("eval_count"),
            total_duration_ms=(
                round(total_duration / 1_000_000, 2)
                if total_duration is not None
                else None
            ),
        )

        _record_generation_usage(
            response=response
        )

        _record_generation_success(
            provider=provider_name,
            backend="ollama",
            started_at=started_at,
        )

        return response

    if provider_config["backend"] == "deepseek":
        started_at = perf_counter()

        try:
            result = await deepseek_provider.generate(
                model=provider_config["model"],
                prompt=request.prompt,
                max_output_tokens=limits.max_output_tokens,
            )
        except DeepSeekProviderError as exc:
            _record_generation_outcome(
                provider=provider_name,
                backend="deepseek",
                outcome="unavailable",
            )

            raise HTTPException(
                status_code=503,
                detail=(
                    "AI provider service unavailable."
                ),
            ) from exc

        usage = result.get("usage", {})
        message = result["choices"][0]["message"]

        completion_details = usage.get(
            "completion_tokens_details",
            {},
        )

        prompt_tokens = usage.get(
            "prompt_tokens",
            0,
        )

        generated_tokens = usage.get(
            "completion_tokens",
            0,
        )

        cache_hit_tokens = usage.get(
            "prompt_cache_hit_tokens",
            0,
        )

        cache_miss_tokens = usage.get(
            "prompt_cache_miss_tokens",
            0,
        )

        cost = estimate_deepseek_cost(
            prompt_tokens=prompt_tokens,
            cache_hit_tokens=cache_hit_tokens,
            cache_miss_tokens=cache_miss_tokens,
            completion_tokens=generated_tokens,
        )

        response = GenerateResponse(
            provider=provider_name,
            backend="deepseek",
            model=provider_config["model"],
            response=message.get("content", ""),
            prompt_tokens=prompt_tokens,
            generated_tokens=generated_tokens,
            reasoning_tokens=completion_details.get(
                "reasoning_tokens"
            ),
            prompt_cache_hit_tokens=cache_hit_tokens,
            prompt_cache_miss_tokens=cache_miss_tokens,
            total_duration_ms=result.get(
                "_gateway_duration_ms"
            ),
            pricing_tier=cost.pricing_tier,
            estimated_cost_usd=cost.estimated_cost_usd,
        )

        _record_generation_usage(
            response=response
        )

        _record_generation_success(
            provider=provider_name,
            backend="deepseek",
            started_at=started_at,
        )

        return response

    _record_generation_outcome(
        provider=provider_name,
        backend="unsupported",
        outcome="unavailable",
    )

    raise HTTPException(
        status_code=501,
        detail=(
            f"Backend '{provider_config['backend']}' "
            "is not implemented."
        ),
    )