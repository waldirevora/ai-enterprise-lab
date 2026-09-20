import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.observability.metrics import (
    METRICS_REGISTRY,
)
from app.rag import service as rag_service


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


def _run_rag():
    return asyncio.run(
        rag_service.generate_rag_answer(
            organization_id=1,
            question="RAG_OUTCOME_TEST",
            question_classification="public",
            allowed_classifications={
                "public",
            },
        )
    )


def _valid_context():
    return SimpleNamespace(
        text="AUTHORIZED_CONTEXT",
        chunks_used=1,
        characters_used=18,
        effective_classification="public",
    )


def test_rag_no_results_records_no_context(
    monkeypatch,
):
    async def fake_retrieve(
        **kwargs,
    ):
        return []

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve,
    )

    labels = {
        "outcome": "no_context",
    }

    before = _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    )

    with pytest.raises(
        rag_service.RagServiceError,
    ):
        _run_rag()

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    ) == before + 1


def test_rag_empty_context_records_no_context(
    monkeypatch,
):
    async def fake_retrieve(
        **kwargs,
    ):
        return [
            object(),
        ]

    def fake_context(
        *args,
        **kwargs,
    ):
        return SimpleNamespace(
            text="",
            chunks_used=0,
            characters_used=0,
            effective_classification="public",
        )

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve,
    )

    monkeypatch.setattr(
        rag_service,
        "build_rag_context",
        fake_context,
    )

    labels = {
        "outcome": "no_context",
    }

    before = _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    )

    with pytest.raises(
        rag_service.RagServiceError,
    ):
        _run_rag()

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    ) == before + 1


def test_rag_missing_classification_records_no_context(
    monkeypatch,
):
    async def fake_retrieve(
        **kwargs,
    ):
        return [
            object(),
        ]

    def fake_context(
        *args,
        **kwargs,
    ):
        return SimpleNamespace(
            text="AUTHORIZED_CONTEXT",
            chunks_used=1,
            characters_used=18,
            effective_classification=None,
        )

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve,
    )

    monkeypatch.setattr(
        rag_service,
        "build_rag_context",
        fake_context,
    )

    labels = {
        "outcome": "no_context",
    }

    before = _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    )

    with pytest.raises(
        rag_service.RagServiceError,
    ):
        _run_rag()

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    ) == before + 1


def test_rag_generation_4xx_records_rejected(
    monkeypatch,
):
    async def fake_retrieve(
        **kwargs,
    ):
        return [
            object(),
        ]

    async def fake_generate(
        request,
    ):
        raise HTTPException(
            status_code=403,
            detail="Policy rejected.",
        )

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve,
    )

    monkeypatch.setattr(
        rag_service,
        "build_rag_context",
        lambda *args, **kwargs: _valid_context(),
    )

    monkeypatch.setattr(
        rag_service.generation,
        "generate_text",
        fake_generate,
    )

    labels = {
        "outcome": "rejected",
    }

    before = _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        _run_rag()

    assert exc_info.value.status_code == 403

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        labels,
    ) == before + 1


def test_rag_generation_5xx_records_unavailable(
    monkeypatch,
):
    async def fake_retrieve(
        **kwargs,
    ):
        return [
            object(),
        ]

    async def fake_generate(
        request,
    ):
        raise HTTPException(
            status_code=503,
            detail="Provider unavailable.",
        )

    monkeypatch.setattr(
        rag_service,
        "retrieve_chunks",
        fake_retrieve,
    )

    monkeypatch.setattr(
        rag_service,
        "build_rag_context",
        lambda *args, **kwargs: _valid_context(),
    )

    monkeypatch.setattr(
        rag_service.generation,
        "generate_text",
        fake_generate,
    )

    unavailable_labels = {
        "outcome": "unavailable",
    }

    rejected_labels = {
        "outcome": "rejected",
    }

    unavailable_before = _metric_value(
        "ai_enterprise_rag_requests_total",
        unavailable_labels,
    )

    rejected_before = _metric_value(
        "ai_enterprise_rag_requests_total",
        rejected_labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        _run_rag()

    assert exc_info.value.status_code == 503

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        unavailable_labels,
    ) == unavailable_before + 1

    assert _metric_value(
        "ai_enterprise_rag_requests_total",
        rejected_labels,
    ) == rejected_before
