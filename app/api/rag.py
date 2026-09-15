from fastapi import APIRouter, HTTPException

from app.rag.schemas import (
    RagCitation,
    RagGenerateRequest,
    RagGenerateResponse,
)
from app.rag.service import (
    RagServiceError,
    generate_rag_answer,
)


router = APIRouter(
    prefix="/v1/rag",
    tags=["rag"],
)


@router.post(
    "/generate",
    response_model=RagGenerateResponse,
)
async def generate_public_rag(
    request: RagGenerateRequest,
) -> RagGenerateResponse:
    try:
        result = await generate_rag_answer(
            question=request.question,

            # Segurança:
            # até existir autenticação/autorização,
            # o endpoint HTTP só acessa dados públicos.
            question_classification="public",
            allowed_classifications={"public"},

            provider=request.provider,
            external_approved=request.external_approved,
            retrieval_limit=request.retrieval_limit,
            max_context_chunks=request.max_context_chunks,
            max_context_characters=(
                request.max_context_characters
            ),
            temperature=request.temperature,
            num_ctx=request.num_ctx,
            max_output_tokens=request.max_output_tokens,
        )

    except RagServiceError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

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