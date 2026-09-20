from collections.abc import Collection
from dataclasses import dataclass

from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.rag.context_builder import (
    RagContext,
    build_rag_context,
)
from app.rag.retrieval import (
    RagRetrievalError,
    RagSearchResult,
    retrieve_chunks,
)


class AgentToolError(Exception):
    pass


@dataclass(frozen=True)
class EnterpriseKnowledgeSearchResult:
    retrieved_chunks: tuple[
        RagSearchResult,
        ...,
    ]

    context: RagContext


async def search_enterprise_knowledge(
    *,
    organization_id: int,
    principal_id: int,
    query: str,
    allowed_classifications: Collection[str],
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ] = (),
    retrieval_limit: int = 5,
    max_context_chunks: int = 5,
    max_context_characters: int = 8000,
) -> EnterpriseKnowledgeSearchResult:
    if organization_id < 1:
        raise AgentToolError(
            "Invalid agent authority."
        )

    if principal_id < 1:
        raise AgentToolError(
            "Invalid agent authority."
        )

    try:
        results = await retrieve_chunks(
            organization_id=organization_id,
            query=query,
            allowed_classifications=(
                frozenset(
                    allowed_classifications
                )
            ),
            limit=retrieval_limit,
            unit_grants=unit_grants,
            principal_id=principal_id,
        )

    except RagRetrievalError as exc:
        raise AgentToolError(
            "Enterprise knowledge search unavailable."
        ) from exc

    context = build_rag_context(
        results,
        max_chunks=max_context_chunks,
        max_characters=(
            max_context_characters
        ),
    )

    used_results = tuple(
        results[:context.chunks_used]
    )

    return EnterpriseKnowledgeSearchResult(
        retrieved_chunks=used_results,
        context=context,
    )
