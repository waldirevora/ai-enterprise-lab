from dataclasses import dataclass

from app.rag.retrieval import RagSearchResult


CLASSIFICATION_PRIORITY = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
}


@dataclass(frozen=True)
class RagContext:
    text: str
    chunks_used: int
    characters_used: int
    effective_classification: str | None
    document_ids: tuple[int, ...]


def _get_effective_classification(
    results: list[RagSearchResult],
) -> str | None:
    if not results:
        return None

    return max(
        (
            result.classification
            for result in results
        ),
        key=lambda value: CLASSIFICATION_PRIORITY[value],
    )


def _format_chunk(
    *,
    result: RagSearchResult,
    position: int,
) -> str:
    return (
        f"[DOCUMENT {position}]\n"
        f"title: {result.title}\n"
        f"source: {result.source}\n"
        f"classification: {result.classification}\n"
        f"chunk_index: {result.chunk_index}\n"
        f"similarity: {result.similarity:.4f}\n"
        "content:\n"
        f"{result.content}\n"
        f"[/DOCUMENT {position}]"
    )


def build_rag_context(
    results: list[RagSearchResult],
    *,
    max_chunks: int = 5,
    max_characters: int = 12000,
) -> RagContext:
    if max_chunks < 1 or max_chunks > 20:
        raise ValueError(
            "max_chunks must be between 1 and 20."
        )

    if max_characters < 1:
        raise ValueError(
            "max_characters must be greater than zero."
        )

    selected: list[RagSearchResult] = []
    blocks: list[str] = []

    for result in results[:max_chunks]:
        block = _format_chunk(
            result=result,
            position=len(selected) + 1,
        )

        candidate = "\n\n".join(
            [*blocks, block]
        )

        if len(candidate) > max_characters:
            break

        blocks.append(block)
        selected.append(result)

    context_text = "\n\n".join(blocks)

    document_ids = tuple(
        dict.fromkeys(
            result.document_id
            for result in selected
        )
    )

    return RagContext(
        text=context_text,
        chunks_used=len(selected),
        characters_used=len(context_text),
        effective_classification=(
            _get_effective_classification(
                selected
            )
        ),
        document_ids=document_ids,
    )