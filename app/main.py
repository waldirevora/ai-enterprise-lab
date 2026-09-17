from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
)

from app.api.rag import router as rag_router
from app.audit.logger import emit_audit_event
from app.audit.middleware import (
    AuditRequestContextMiddleware,
)
from app.core.config import settings
from app.providers.catalog import get_provider_catalog
from app.rate_limit.http import enforce_rate_limit
from app.rate_limit.origin import (
    RateLimitOriginError,
    build_origin_key,
)
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
)
from app.services.generation import generate_text


app = FastAPI(
    title="AI Enterprise Lab Gateway",
    version="0.1.0",
)

app.add_middleware(
    AuditRequestContextMiddleware
)

app.include_router(rag_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/v1/providers")
def providers() -> dict:
    return get_provider_catalog()


@app.post(
    "/v1/generate",
    response_model=GenerateResponse,
)
async def generate(
    request: GenerateRequest,
    http_request: Request,
) -> GenerateResponse:
    try:
        rate_limit_key = build_origin_key(
            namespace="public-generate",
            request=http_request,
        )

    except RateLimitOriginError as exc:
        emit_audit_event(
            event_type=(
                "rate_limit.unavailable"
            ),
            outcome="unavailable",
            reason_code=(
                "rate_limit_origin_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        #
        # Fail closed.
        #
        # Se não conseguimos identificar
        # a origem da requisição, não
        # permitimos bypass do limiter.
        #
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Rate limit service unavailable."
            ),
        ) from exc

    await enforce_rate_limit(
        key=rate_limit_key,
        rate_per_minute=(
            settings
            .rate_limit_public_generate_per_minute
        ),
        burst=(
            settings
            .rate_limit_public_generate_burst
        ),
    )

    return await generate_text(
        request
    )