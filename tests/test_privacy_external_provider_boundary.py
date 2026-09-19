import asyncio

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.rag.context_builder import RagContext
from app.rag.retrieval import RagSearchResult
from app.rag.service import generate_rag_answer


def _make_result(
    *,
    classification: str,
) -> RagSearchResult:
    return RagSearchResult(
        chunk_id=1,
        document_id=10,
        title="Documento",
        source="test",
        source_uri=None,
        classification=classification,
        chunk_index=0,
        content="CONTEUDO_PRIVADO",
        metadata={},
        similarity=0.99,
    )


@pytest.mark.parametrize(
    "context_classification",
    [
        "internal",
        "confidential",
    ],
)
def test_external_provider_is_blocked_for_non_public_rag_context(
    monkeypatch,
    context_classification,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    async def fake_retrieve_chunks(
        **kwargs,
    ):
        return (
            _make_result(
                classification=context_classification,
            ),
        )

    async def should_not_call_deepseek(
        **kwargs,
    ):
        raise AssertionError(
            "DeepSeek must not receive non-public RAG context."
        )

    monkeypatch.setattr(
        "app.rag.service.retrieve_chunks",
        fake_retrieve_chunks,
    )

    monkeypatch.setattr(
        "app.services.generation.deepseek_provider.generate",
        should_not_call_deepseek,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            generate_rag_answer(
                organization_id=1,
                principal_id=1,
                question="teste",
                question_classification="public",
                allowed_classifications={
                    "public",
                    "internal",
                    "confidential",
                },
                provider="external_deep",
                external_approved=True,
                retrieval_limit=5,
                max_context_chunks=5,
                max_context_characters=8000,
                temperature=0.0,
                num_ctx=4096,
                max_output_tokens=64,
            )
        )

    assert exc_info.value.status_code == 403


def test_external_provider_can_process_public_rag_context_when_approved(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    async def fake_retrieve_chunks(
        **kwargs,
    ):
        return (
            _make_result(
                classification="public",
            ),
        )

    called = {}

    async def fake_deepseek_generate(
        *,
        model,
        prompt,
        max_output_tokens,
    ):
        called["prompt"] = prompt

        return {
            "choices": [
                {
                    "message": {
                        "content": "ok",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 1,
                "completion_tokens_details": {},
            },
            "_gateway_duration_ms": 1.0,
        }

    monkeypatch.setattr(
        "app.rag.service.retrieve_chunks",
        fake_retrieve_chunks,
    )

    monkeypatch.setattr(
        "app.services.generation.deepseek_provider.generate",
        fake_deepseek_generate,
    )

    result = asyncio.run(
        generate_rag_answer(
            organization_id=1,
            principal_id=1,
            question="teste",
            question_classification="public",
            allowed_classifications={
                "public",
            },
            provider="external_deep",
            external_approved=True,
            retrieval_limit=5,
            max_context_chunks=5,
            max_context_characters=8000,
            temperature=0.0,
            num_ctx=4096,
            max_output_tokens=64,
        )
    )

    assert result.effective_classification == "public"
    assert "CONTEUDO_PRIVADO" in called["prompt"]
