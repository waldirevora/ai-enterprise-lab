import asyncio
from types import SimpleNamespace

from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.rag import service as rag_service
from app.schemas import GenerateResponse


def _metric_value(
    name: str,
    labels: dict[str, str],
) -> float:
    value = METRICS_REGISTRY.get_sample_value(
        name,
        labels,
    )

    return float(
        value or 0.0
    )


def test_successful_rag_records_metrics(
    monkeypatch,
):
    async def fake_retrieve_chunks(
        **kwargs,
    ):
        return [
            object(),
            object(),
        ]

    def fake_build_rag_context(
        results,
        *,
        max_chunks,
        max_characters,
    ):
        return SimpleNamespace(
            text="AUTHORIZED_CONTEXT",
            chunks_used=2,
            characters_used=18,
            effective_classification="public",
        )

    async def fake_generate_text(
        request,
    ):
        return GenerateResponse(
            provider="local_fast",
            backend="ollama",
            model="test-model",
            response="RAG_OK",
            prompt_tokens=10,
            generated_tokens=4,
            total_duration_ms=20.0,
        )

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve_chunks,
    )

    monkeypatch.setattr(
        rag_service,
        "build_rag_context",
        fake_build_rag_context,
    )

    monkeypatch.setattr(
        rag_service.generation,
        "generate_text",
        fake_generate_text,
    )

    labels = {
        "outcome": "success",
    }

    requests_before = _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    )

    retrieval_count_before = _metric_value(
        "ai_enterprise_rag_retrieval_duration_seconds_count",
        labels,
    )

    chunks_count_before = _metric_value(
        "ai_enterprise_rag_chunks_used_count",
        labels,
    )

    chunks_sum_before = _metric_value(
        "ai_enterprise_rag_chunks_used_sum",
        labels,
    )

    result = asyncio.run(
        rag_service.generate_rag_answer(
            organization_id=1,
            question="METRICS_TEST",
            question_classification="public",
            allowed_classifications={
                "public",
            },
            retrieval_limit=5,
            max_context_chunks=5,
            max_context_characters=8000,
        )
    )

    assert result.generation.response == "RAG_OK"

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    ) == requests_before + 1

    assert _metric_value(
        "ai_enterprise_rag_retrieval_duration_seconds_count",
        labels,
    ) == retrieval_count_before + 1

    assert _metric_value(
        "ai_enterprise_rag_chunks_used_count",
        labels,
    ) == chunks_count_before + 1

    assert _metric_value(
        "ai_enterprise_rag_chunks_used_sum",
        labels,
    ) == chunks_sum_before + 2
