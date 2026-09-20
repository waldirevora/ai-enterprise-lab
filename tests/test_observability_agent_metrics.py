import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.agents import service as agent_service
from app.agents.schemas import (
    AgentRunRequest,
)
from app.agents.tools import (
    AgentToolError,
)
from app.observability.metrics import (
    METRICS_REGISTRY,
)
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


def _valid_tool_result():
    return SimpleNamespace(
        retrieved_chunks=(),
        context=SimpleNamespace(
            text="AUTHORIZED_CONTEXT",
            chunks_used=1,
            characters_used=18,
            effective_classification="public",
        ),
    )


def _run_agent():
    return asyncio.run(
        agent_service.run_enterprise_knowledge_agent(
            request=AgentRunRequest(
                message="AGENT_METRICS_TEST",
                provider="local_fast",
            ),
            organization_id=1,
            principal_id=1,
            question_classification="public",
            allowed_classifications={
                "public",
            },
        )
    )


def test_successful_agent_run_records_metrics(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return _valid_tool_result()

    async def fake_generate(
        request,
    ):
        return GenerateResponse(
            provider="local_fast",
            backend="ollama",
            model="test-model",
            response="AGENT_OK",
            prompt_tokens=10,
            generated_tokens=4,
            total_duration_ms=20.0,
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        agent_service,
        "generate_text",
        fake_generate,
    )

    labels = {
        "outcome": "success",
    }

    runs_before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    duration_count_before = _metric_value(
        "ai_enterprise_agent_run_duration_seconds_count",
        labels,
    )

    response = _run_agent()

    assert response.answer == "AGENT_OK"

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == runs_before + 1

    assert _metric_value(
        "ai_enterprise_agent_run_duration_seconds_count",
        labels,
    ) == duration_count_before + 1


def test_agent_tool_unavailable_records_unavailable(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        raise AgentToolError(
            "internal detail"
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    labels = {
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    with pytest.raises(
        agent_service.AgentServiceError,
    ):
        _run_agent()

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == before + 1


def test_agent_no_context_records_no_context(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return SimpleNamespace(
            retrieved_chunks=(),
            context=SimpleNamespace(
                text="",
                chunks_used=0,
                characters_used=0,
                effective_classification=None,
            ),
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    labels = {
        "outcome": "no_context",
    }

    before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    with pytest.raises(
        agent_service.AgentNoContextError,
    ):
        _run_agent()

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == before + 1


def test_agent_generation_4xx_records_rejected(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return _valid_tool_result()

    async def fake_generate(
        request,
    ):
        raise HTTPException(
            status_code=403,
            detail="Policy rejected.",
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        agent_service,
        "generate_text",
        fake_generate,
    )

    labels = {
        "outcome": "rejected",
    }

    before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        _run_agent()

    assert exc_info.value.status_code == 403

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == before + 1


def test_agent_generation_5xx_records_unavailable(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return _valid_tool_result()

    async def fake_generate(
        request,
    ):
        raise HTTPException(
            status_code=503,
            detail="Provider unavailable.",
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        agent_service,
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
        "ai_enterprise_agent_runs_total",
        unavailable_labels,
    )

    rejected_before = _metric_value(
        "ai_enterprise_agent_runs_total",
        rejected_labels,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        _run_agent()

    assert exc_info.value.status_code == 503

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        unavailable_labels,
    ) == unavailable_before + 1

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        rejected_labels,
    ) == rejected_before

def test_agent_tool_timeout_records_unavailable(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        raise TimeoutError(
            "tool timeout detail"
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    labels = {
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    with pytest.raises(
        agent_service.AgentServiceError,
    ) as exc_info:
        _run_agent()

    assert str(
        exc_info.value
    ) == (
        "Agent tool service unavailable."
    )

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == before + 1


def test_agent_generation_timeout_records_unavailable(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return _valid_tool_result()

    async def fake_generate(
        request,
    ):
        raise TimeoutError(
            "generation timeout detail"
        )

    monkeypatch.setattr(
        agent_service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        agent_service,
        "generate_text",
        fake_generate,
    )

    labels = {
        "outcome": "unavailable",
    }

    before = _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    )

    with pytest.raises(
        agent_service.AgentServiceError,
    ) as exc_info:
        _run_agent()

    assert str(
        exc_info.value
    ) == (
        "Agent generation service unavailable."
    )

    assert _metric_value(
        "ai_enterprise_agent_runs_total",
        labels,
    ) == before + 1
