from fastapi import HTTPException

from app.audit.logger import emit_audit_event
from app.core.config import ProviderName, settings
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
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    catalog = get_provider_catalog()
    provider_config = catalog["providers"][provider_name]

    if provider_config["backend"] == "ollama":
        try:
            result = await ollama_provider.generate(
                model=provider_config["model"],
                prompt=request.prompt,
                temperature=request.temperature,
                num_ctx=request.num_ctx,
                max_output_tokens=limits.max_output_tokens,
            )
        except OllamaProviderError as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
            ) from exc

        total_duration = result.get("total_duration")

        return GenerateResponse(
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

    if provider_config["backend"] == "deepseek":
        try:
            result = await deepseek_provider.generate(
                model=provider_config["model"],
                prompt=request.prompt,
                max_output_tokens=limits.max_output_tokens,
            )
        except DeepSeekProviderError as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
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

        return GenerateResponse(
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

    raise HTTPException(
        status_code=501,
        detail=(
            f"Backend '{provider_config['backend']}' "
            "is not implemented."
        ),
    )