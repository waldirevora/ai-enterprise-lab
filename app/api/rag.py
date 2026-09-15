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

            # Endpoint público permanece estritamente
            # limitado a conteúdo público.
            question_classification="public",
            allowed_classifications={"public"},

            provider=request.provider,
            external_approved=(
                request.external_approved
            ),
            retrieval_limit=request.retrieval_limit,
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
        result = await generate_rag_answer(
            # Segurança:
            # tenant vem exclusivamente da identidade
            # autenticada.
            organization_id=(
                context.organization_id
            ),

            question=request.question,

            # Política conservadora nesta fase:
            # classificamos a pergunta no teto de
            # sensibilidade do principal.
            #
            # Isso impede que um cliente tente
            # subdeclarar uma pergunta confidencial
            # como pública para usar provider externo.
            question_classification=(
                context.max_classification
            ),

            # O cliente não controla esta lista.
            allowed_classifications=(
                context.allowed_classifications
            ),

            provider=request.provider,
            external_approved=(
                request.external_approved
            ),
            retrieval_limit=request.retrieval_limit,
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