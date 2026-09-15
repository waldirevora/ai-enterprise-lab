from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.access.context import PrincipalContext
from app.access.dependencies import (
    require_principal_context,
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
from app.rag.schemas import (
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
    response_model=RagGenerateResponse,
)
async def generate_public_rag(
    request: RagGenerateRequest,
) -> RagGenerateResponse:
    organization_id = (
        await _resolve_public_organization_id()
    )

    try:
        result = await generate_rag_answer(
            organization_id=organization_id,
            question=request.question,

            # Endpoint público permanece
            # estritamente public-only e
            # corporate-only.
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
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _build_response(result)


@router.post(
    "/generate-authenticated",
    response_model=RagGenerateResponse,
)
async def generate_authenticated_rag(
    request: RagGenerateRequest,
    context: PrincipalContext = Depends(
        require_principal_context
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
        #    referências explícitas a units.
        #
        # Exemplos:
        #
        # Financeiro pergunta RH sem grant:
        # → deny aqui
        # → retrieval não roda
        # → LLM não roda
        #
        # Financeiro pergunta Financeiro:
        # → grants são reduzidos para Financeiro
        #
        scope_decision = await resolve_unit_scope(
            context=context,
            question=request.question,
            unit_grants=unit_grants,
        )

        #
        # 3. Só depois do authorization scope
        #    o RAG pode ser executado.
        #
        result = await generate_rag_answer(
            organization_id=(
                context.organization_id
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
        #
        # Resposta propositalmente genérica.
        # Não revela se a unit existe ou se
        # apenas não está autorizada.
        #
        raise HTTPException(
            status_code=404,
            detail=(
                "No authorized RAG context was found."
            ),
        ) from exc

    except UnitScopeUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unit scope service unavailable."
            ),
        ) from exc

    except UnitGrantUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unit authorization service unavailable."
            ),
        ) from exc

    except RagServiceError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _build_response(result)