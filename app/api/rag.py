from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from app.access.context import PrincipalContext
from app.audit.logger import emit_audit_event
from app.access.dependencies import (
    require_rate_limited_principal_context,
)
from app.access.organizations import (
    OrganizationResolutionError,
    resolve_organization_id,
)
from app.access.unit_grants import (
    UnitGrantUnavailableError,
    load_unit_access_grants,
)
from app.access.unit_scope import (
    UnitScopeDeniedError,
    UnitScopeUnavailableError,
    resolve_unit_scope,
)
from app.core.config import settings
from app.rate_limit.http import enforce_rate_limit
from app.rate_limit.origin import (
    RateLimitOriginError,
    build_origin_key,
)
from app.rag.schemas import (
    PublicRagCitation,
    PublicRagGenerateResponse,
    RagCitation,
    RagGenerateRequest,
    RagGenerateResponse,
)
from app.rag.service import (
    RagGenerationResult,
    RagServiceError,
    generate_rag_answer,
)


router = APIRouter(
    prefix="/v1/rag",
    tags=["rag"],
)


async def _resolve_public_organization_id() -> int:
    try:
        return await resolve_organization_id(
            settings.ai_default_organization_slug
        )

    except OrganizationResolutionError as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG organization is unavailable.",
        ) from exc


def _rag_service_http_exception(
    exc: RagServiceError,
) -> HTTPException:
    if (
        str(exc)
        == "No authorized RAG context was found."
    ):
        return HTTPException(
            status_code=404,
            detail=(
                "No authorized RAG context was found."
            ),
        )

    return HTTPException(
        status_code=503,
        detail="RAG service unavailable.",
    )


def _build_public_response(
    result: RagGenerationResult,
) -> PublicRagGenerateResponse:
    generation = result.generation

    citations = [
        PublicRagCitation(
            title=item.title,
            source=item.source,
        )
        for item in result.retrieved_chunks
    ]

    return PublicRagGenerateResponse(
        answer=generation.response,
        provider=generation.provider,
        backend=generation.backend,
        model=generation.model,
        effective_classification=(
            result.effective_classification
        ),
        citations=citations,
        prompt_tokens=generation.prompt_tokens,
        generated_tokens=generation.generated_tokens,
        reasoning_tokens=generation.reasoning_tokens,
        total_duration_ms=generation.total_duration_ms,
        pricing_tier=generation.pricing_tier,
        estimated_cost_usd=(
            generation.estimated_cost_usd
        ),
    )


def _build_response(
    result: RagGenerationResult,
) -> RagGenerateResponse:
    generation = result.generation

    citations = [
        RagCitation(
            document_id=item.document_id,
            title=item.title,
            source=item.source,
            classification=item.classification,
            chunk_index=item.chunk_index,
            similarity=item.similarity,
        )
        for item in result.retrieved_chunks
    ]

    return RagGenerateResponse(
        answer=generation.response,
        provider=generation.provider,
        backend=generation.backend,
        model=generation.model,
        effective_classification=(
            result.effective_classification
        ),
        citations=citations,
        prompt_tokens=generation.prompt_tokens,
        generated_tokens=generation.generated_tokens,
        reasoning_tokens=generation.reasoning_tokens,
        total_duration_ms=generation.total_duration_ms,
        pricing_tier=generation.pricing_tier,
        estimated_cost_usd=(
            generation.estimated_cost_usd
        ),
    )


@router.post(
    "/generate",
    response_model=PublicRagGenerateResponse,
)
async def generate_public_rag(
    request: RagGenerateRequest,
    http_request: Request,
) -> PublicRagGenerateResponse:
    #
    # Rate limit público ocorre antes de
    # resolver organization, retrieval e LLM.
    #
    try:
        rate_limit_key = build_origin_key(
            namespace="public-rag",
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
            .rate_limit_public_rag_per_minute
        ),
        burst=(
            settings
            .rate_limit_public_rag_burst
        ),
    )

    organization_id = (
        await _resolve_public_organization_id()
    )

    try:
        result = await generate_rag_answer(
            organization_id=organization_id,
            question=request.question,

            #
            # Endpoint público permanece
            # estritamente public-only e
            # corporate-only.
            #
            question_classification="public",
            allowed_classifications={
                "public"
            },

            provider=request.provider,
            external_approved=(
                request.external_approved
            ),
            retrieval_limit=(
                request.retrieval_limit
            ),
            max_context_chunks=(
                request.max_context_chunks
            ),
            max_context_characters=(
                request.max_context_characters
            ),
            temperature=request.temperature,
            num_ctx=request.num_ctx,
            max_output_tokens=(
                request.max_output_tokens
            ),
        )

    except RagServiceError as exc:
        raise _rag_service_http_exception(
            exc
        ) from exc

    return _build_public_response(result)


@router.post(
    "/generate-authenticated",
    response_model=RagGenerateResponse,
)
async def generate_authenticated_rag(
    request: RagGenerateRequest,
    context: PrincipalContext = Depends(
        require_rate_limited_principal_context
    ),
) -> RagGenerateResponse:
    try:
        #
        # 1. Carrega grants reais do principal.
        #
        unit_grants = await load_unit_access_grants(
            context
        )

        #
        # 2. Resolve deterministicamente
        # referências explícitas a units.
        #
        scope_decision = await resolve_unit_scope(
            context=context,
            question=request.question,
            unit_grants=unit_grants,
        )

        #
        # 3. Só depois do authorization scope
        # o RAG pode ser executado.
        #
        result = await generate_rag_answer(
            organization_id=(
                context.organization_id
            ),

            principal_id=(
                context.principal_id
            ),

            question=request.question,

            question_classification=(
                context.max_classification
            ),

            allowed_classifications=(
                context.allowed_classifications
            ),

            unit_grants=(
                scope_decision.unit_grants
            ),

            provider=request.provider,
            external_approved=(
                request.external_approved
            ),
            retrieval_limit=(
                request.retrieval_limit
            ),
            max_context_chunks=(
                request.max_context_chunks
            ),
            max_context_characters=(
                request.max_context_characters
            ),
            temperature=request.temperature,
            num_ctx=request.num_ctx,
            max_output_tokens=(
                request.max_output_tokens
            ),
        )

    except UnitScopeDeniedError as exc:
        emit_audit_event(
            event_type=(
                "authorization.unit_scope_denied"
            ),
            outcome="denied",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            reason_code=(
                "unit_scope_denied"
            ),
            metadata={
                "status_code": 404,
            },
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "No authorized RAG context was found."
            ),
        ) from exc

    except UnitScopeUnavailableError as exc:
        emit_audit_event(
            event_type=(
                "authorization.unit_scope_unavailable"
            ),
            outcome="unavailable",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            reason_code=(
                "unit_scope_backend_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Unit scope service unavailable."
            ),
        ) from exc

    except UnitGrantUnavailableError as exc:
        emit_audit_event(
            event_type=(
                "authorization.unit_grants_unavailable"
            ),
            outcome="unavailable",
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
            reason_code=(
                "unit_grants_backend_unavailable"
            ),
            metadata={
                "status_code": 503,
            },
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Unit authorization service unavailable."
            ),
        ) from exc

    except RagServiceError as exc:
        if (
            str(exc)
            == "No authorized RAG context was found."
        ):
            emit_audit_event(
                event_type=(
                    "rag.authorized_context_not_found"
                ),
                outcome="failure",
                organization_id=(
                    context.organization_id
                ),
                principal_id=(
                    context.principal_id
                ),
                reason_code=(
                    "authorized_context_not_found"
                ),
                metadata={
                    "status_code": 404,
                },
            )

        raise _rag_service_http_exception(
            exc
        ) from exc

    emit_audit_event(
        event_type=(
            "rag.authenticated.success"
        ),
        outcome="success",
        organization_id=(
            context.organization_id
        ),
        principal_id=(
            context.principal_id
        ),
        provider=(
            result.generation.provider
        ),
        classification=(
            result.effective_classification
        ),
        reason_code=(
            "authenticated_rag_completed"
        ),
        metadata={
            "status_code": 200,
            "retrieved_chunks": len(
                result.retrieved_chunks
            ),
        },
    )

    return _build_response(result)
