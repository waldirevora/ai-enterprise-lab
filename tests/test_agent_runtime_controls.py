import asyncio

import pytest
from fastapi import HTTPException

from app.agents import service
from app.agents.schemas import (
    AgentRunRequest,
)
from app.agents.service import (
    AgentNoContextError,
    AgentServiceError,
    run_enterprise_knowledge_agent,
)
from app.agents.tools import (
    AgentToolError,
    EnterpriseKnowledgeSearchResult,
)
from app.rag.context_builder import (
    RagContext,
)
from app.rag.retrieval import (
    RagSearchResult,
)
from app.schemas import GenerateResponse


def make_tool_result():
    chunk = RagSearchResult(
        chunk_id=10,
        document_id=5,
        title="Documento",
        source="agent-runtime-test",
        source_uri=None,
        classification="internal",
        chunk_index=0,
        content="CONTEUDO_AUTORIZADO",
        metadata={},
        similarity=0.95,
    )

    return EnterpriseKnowledgeSearchResult(
        retrieved_chunks=(chunk,),
        context=RagContext(
            text="CONTEXTO_AUTORIZADO",
            chunks_used=1,
            characters_used=19,
            effective_classification=(
                "internal"
            ),
            document_ids=(5,),
        ),
    )


def make_generation():
    return GenerateResponse(
        provider="local_fast",
        backend="ollama",
        model="test-model",
        response="RESPOSTA",
    )


def capture_audit(
    monkeypatch,
):
    events = []

    def fake_emit_audit_event(
        **kwargs,
    ):
        events.append(kwargs)

    monkeypatch.setattr(
        service,
        "emit_audit_event",
        fake_emit_audit_event,
    )

    return events


def test_tool_timeout_is_sanitized_and_audited(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    never = asyncio.Event()

    async def slow_search(
        **kwargs,
    ):
        await never.wait()

    async def should_not_generate(
        request,
    ):
        raise AssertionError(
            "Generation must not run "
            "after tool timeout."
        )

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        slow_search,
    )

    monkeypatch.setattr(
        service,
        "generate_text",
        should_not_generate,
    )

    monkeypatch.setattr(
        service,
        "AGENT_TOOL_TIMEOUT_SECONDS",
        0.001,
    )

    with pytest.raises(
        AgentServiceError,
        match=(
            "Agent tool service unavailable"
        ),
    ):
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste"
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "internal"
                ),
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert events == [
        {
            "event_type": (
                "agent.tool.timeout"
            ),
            "outcome": "unavailable",
            "organization_id": 42,
            "principal_id": 10,
            "classification": (
                "internal"
            ),
            "reason_code": (
                "enterprise_knowledge_timeout"
            ),
            "metadata": {
                "status_code": 503,
            },
        }
    ]


def test_tool_failure_is_audited_without_private_detail(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    async def failing_search(
        **kwargs,
    ):
        raise AgentToolError(
            "PRIVATE_TOOL_DETAIL"
        )

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        failing_search,
    )

    with pytest.raises(
        AgentServiceError,
    ) as exc_info:
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste"
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "internal"
                ),
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert (
        "PRIVATE_TOOL_DETAIL"
        not in str(
            exc_info.value
        )
    )

    assert (
        events[0]["event_type"]
        == "agent.tool.unavailable"
    )

    assert (
        "PRIVATE_TOOL_DETAIL"
        not in str(events)
    )


def test_empty_context_is_audited(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    async def empty_search(
        **kwargs,
    ):
        return EnterpriseKnowledgeSearchResult(
            retrieved_chunks=(),
            context=RagContext(
                text="",
                chunks_used=0,
                characters_used=0,
                effective_classification=None,
                document_ids=(),
            ),
        )

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        empty_search,
    )

    with pytest.raises(
        AgentNoContextError,
    ):
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste"
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "internal"
                ),
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert [
        event["event_type"]
        for event in events
    ] == [
        "agent.tool.success",
        "agent.context.empty",
    ]


def test_generation_timeout_is_sanitized_and_audited(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    async def fake_search(
        **kwargs,
    ):
        return make_tool_result()

    never = asyncio.Event()

    async def slow_generate(
        request,
    ):
        await never.wait()

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        service,
        "generate_text",
        slow_generate,
    )

    monkeypatch.setattr(
        service,
        "AGENT_GENERATION_TIMEOUT_SECONDS",
        0.001,
    )

    with pytest.raises(
        AgentServiceError,
        match=(
            "Agent generation service "
            "unavailable"
        ),
    ):
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste"
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "internal"
                ),
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert [
        event["event_type"]
        for event in events
    ] == [
        "agent.tool.success",
        "agent.generation.timeout",
    ]


def test_provider_rejection_is_preserved_and_audited(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    async def fake_search(
        **kwargs,
    ):
        return make_tool_result()

    async def reject_generation(
        request,
    ):
        raise HTTPException(
            status_code=403,
            detail="Provider blocked.",
        )

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        service,
        "generate_text",
        reject_generation,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste"
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "internal"
                ),
                allowed_classifications={
                    "internal"
                },
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert [
        event["event_type"]
        for event in events
    ] == [
        "agent.tool.success",
        "agent.generation.rejected",
    ]


def test_successful_agent_run_is_audited(
    monkeypatch,
):
    events = capture_audit(
        monkeypatch
    )

    async def fake_search(
        **kwargs,
    ):
        return make_tool_result()

    async def fake_generate(
        request,
    ):
        return make_generation()

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        service,
        "generate_text",
        fake_generate,
    )

    result = asyncio.run(
        run_enterprise_knowledge_agent(
            request=AgentRunRequest(
                message="teste"
            ),
            organization_id=42,
            principal_id=10,
            question_classification=(
                "internal"
            ),
            allowed_classifications={
                "internal"
            },
        )
    )

    assert result.answer == "RESPOSTA"

    assert [
        event["event_type"]
        for event in events
    ] == [
        "agent.tool.success",
        "agent.run.success",
    ]

    final_event = events[-1]

    assert (
        final_event["organization_id"]
        == 42
    )

    assert (
        final_event["principal_id"]
        == 10
    )

    assert (
        final_event["classification"]
        == "internal"
    )

    assert (
        final_event["provider"]
        == "local_fast"
    )
