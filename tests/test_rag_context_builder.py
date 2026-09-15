import pytest

from app.rag.context_builder import (
    build_rag_context,
)
from app.rag.retrieval import RagSearchResult


def make_result(
    *,
    document_id: int,
    classification: str,
    content: str,
    similarity: float = 0.9,
) -> RagSearchResult:
    return RagSearchResult(
        chunk_id=document_id * 10,
        document_id=document_id,
        title=f"Documento {document_id}",
        source=f"source-{document_id}",
        source_uri=None,
        classification=classification,
        chunk_index=0,
        content=content,
        metadata={
            "private_metadata": "must-not-leak",
        },
        similarity=similarity,
    )


def test_empty_results_create_empty_context():
    context = build_rag_context([])

    assert context.text == ""
    assert context.chunks_used == 0
    assert context.characters_used == 0
    assert context.effective_classification is None
    assert context.document_ids == ()


def test_context_preserves_retrieval_order():
    results = [
        make_result(
            document_id=1,
            classification="public",
            content="Primeiro resultado",
            similarity=0.95,
        ),
        make_result(
            document_id=2,
            classification="public",
            content="Segundo resultado",
            similarity=0.80,
        ),
    ]

    context = build_rag_context(results)

    first_position = context.text.index(
        "Primeiro resultado"
    )

    second_position = context.text.index(
        "Segundo resultado"
    )

    assert first_position < second_position


def test_context_uses_highest_classification():
    results = [
        make_result(
            document_id=1,
            classification="public",
            content="Publico",
        ),
        make_result(
            document_id=2,
            classification="internal",
            content="Interno",
        ),
        make_result(
            document_id=3,
            classification="confidential",
            content="Confidencial",
        ),
    ]

    context = build_rag_context(results)

    assert (
        context.effective_classification
        == "confidential"
    )


def test_context_respects_max_chunks():
    results = [
        make_result(
            document_id=index,
            classification="public",
            content=f"Conteudo {index}",
        )
        for index in range(1, 6)
    ]

    context = build_rag_context(
        results,
        max_chunks=2,
    )

    assert context.chunks_used == 2
    assert "Conteudo 1" in context.text
    assert "Conteudo 2" in context.text
    assert "Conteudo 3" not in context.text


def test_context_does_not_expose_arbitrary_metadata():
    result = make_result(
        document_id=1,
        classification="internal",
        content="Conteudo autorizado",
    )

    context = build_rag_context([result])

    assert "Conteudo autorizado" in context.text
    assert "private_metadata" not in context.text
    assert "must-not-leak" not in context.text


def test_context_respects_character_limit():
    results = [
        make_result(
            document_id=1,
            classification="public",
            content="A" * 100,
        ),
        make_result(
            document_id=2,
            classification="public",
            content="B" * 100,
        ),
    ]

    full_context = build_rag_context(
        results,
        max_characters=10000,
    )

    first_only = build_rag_context(
        results,
        max_chunks=1,
        max_characters=10000,
    )

    limited_context = build_rag_context(
        results,
        max_characters=(
            first_only.characters_used + 1
        ),
    )

    assert full_context.chunks_used == 2
    assert limited_context.chunks_used == 1
    assert (
        limited_context.characters_used
        <= first_only.characters_used + 1
    )


def test_invalid_limits_are_rejected():
    with pytest.raises(
        ValueError,
        match="max_chunks",
    ):
        build_rag_context(
            [],
            max_chunks=0,
        )

    with pytest.raises(
        ValueError,
        match="max_characters",
    ):
        build_rag_context(
            [],
            max_characters=0,
        )