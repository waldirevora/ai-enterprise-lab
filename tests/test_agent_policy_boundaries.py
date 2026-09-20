import asyncio

import pytest
from fastapi import HTTPException

from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.agents import service
from app.agents.schemas import (
    AgentRunRequest,
)
from app.agents.service import (
    run_enterprise_knowledge_agent,
)
from app.agents.tools import (
    EnterpriseKnowledgeSearchResult,
)
from app.core.config import settings
from app.rag.context_builder import (
    RagContext,
)
from app.rag.retrieval import (
    RagSearchResult,
)
from app.schemas import GenerateResponse
from app.services import generation


def make_tool_result(
    *,
    classification: str,
) -> EnterpriseKnowledgeSearchResult:
    chunk = RagSearchResult(
        chunk_id=10,
        document_id=5,
        title="Documento Autorizado",
        source="agent-policy-test",
        source_uri=None,
        classification=classification,
        chunk_index=0,
        content="CONTEUDO_AUTORIZADO",
        metadata={},
        similarity=0.95,
    )

    context = RagContext(
        text="CONTEXTO_AUTORIZADO",
        chunks_used=1,
        characters_used=19,
        effective_classification=(
            classification
        ),
        document_ids=(5,),
    )

    return EnterpriseKnowledgeSearchResult(
        retrieved_chunks=(chunk,),
        context=context,
    )


def test_agent_forwards_server_side_authority(
    monkeypatch,
):
    captured = {}

    grant = UnitAccessGrant(
        organizational_unit_id=100,
        unit_slug="financeiro",
        unit_name="Financeiro",
        role="member",
        effective_max_classification=(
            "internal"
        ),
    )

    async def fake_search(
        **kwargs,
    ):
        captured.update(kwargs)

        return make_tool_result(
            classification="internal"
        )

    async def fake_generate(
        request,
    ):
        return GenerateResponse(
            provider="local_fast",
            backend="ollama",
            model="test-model",
            response="OK",
        )

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

    asyncio.run(
        run_enterprise_knowledge_agent(
            request=AgentRunRequest(
                message="teste",
            ),
            organization_id=42,
            principal_id=10,
            question_classification=(
                "internal"
            ),
            allowed_classifications={
                "public",
                "internal",
            },
            unit_grants=(grant,),
        )
    )

    assert (
        captured["organization_id"]
        == 42
    )

    assert (
        captured["principal_id"]
        == 10
    )

    assert (
        captured[
            "allowed_classifications"
        ]
        == {
            "public",
            "internal",
        }
    )

    assert (
        captured["unit_grants"]
        == (grant,)
    )


@pytest.mark.parametrize(
    "classification",
    [
        "internal",
        "confidential",
    ],
)
def test_external_provider_is_blocked_for_non_public_agent_context(
    monkeypatch,
    classification,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    async def fake_search(
        **kwargs,
    ):
        return make_tool_result(
            classification=classification
        )

    async def should_not_call_deepseek(
        **kwargs,
    ):
        raise AssertionError(
            "DeepSeek must not receive "
            "non-public agent context."
        )

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        should_not_call_deepseek,
    )

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        asyncio.run(
            run_enterprise_knowledge_agent(
                request=AgentRunRequest(
                    message="teste",
                    provider=(
                        "external_deep"
                    ),
                    external_approved=True,
                ),
                organization_id=42,
                principal_id=10,
                question_classification=(
                    "public"
                ),
                allowed_classifications={
                    "public",
                    "internal",
                    "confidential",
                },
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )

    assert (
        "not allowed"
        in exc_info.value.detail.lower()
    )


def test_public_agent_context_may_use_external_provider(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "external_ai_enabled",
        True,
    )

    calls = {
        "deepseek": 0,
    }

    async def fake_search(
        **kwargs,
    ):
        return make_tool_result(
            classification="public"
        )

    async def fake_deepseek_generate(
        *,
        model,
        prompt,
        max_output_tokens,
    ):
        calls["deepseek"] += 1

        assert (
            "CONTEXTO_AUTORIZADO"
            in prompt
        )

        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "RESPOSTA_EXTERNA"
                        ),
                        "reasoning_content": (
                            "PRIVATE_REASONING"
                        ),
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 8,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 20,
                "completion_tokens_details": {
                    "reasoning_tokens": 3,
                },
            },
            "_gateway_duration_ms": 100.0,
        }

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        generation.deepseek_provider,
        "generate",
        fake_deepseek_generate,
    )

    result = asyncio.run(
        run_enterprise_knowledge_agent(
            request=AgentRunRequest(
                message="teste",
                provider="external_deep",
                external_approved=True,
            ),
            organization_id=42,
            principal_id=10,
            question_classification=(
                "public"
            ),
            allowed_classifications={
                "public"
            },
        )
    )

    assert calls["deepseek"] == 1

    assert (
        result.provider
        == "external_deep"
    )

    assert (
        result.backend
        == "deepseek"
    )

    assert (
        result.answer
        == "RESPOSTA_EXTERNA"
    )

    assert (
        result.effective_classification
        == "public"
    )

    serialized = (
        result.model_dump_json()
    )

    assert (
        "PRIVATE_REASONING"
        not in serialized
    )


def test_local_provider_allows_confidential_agent_context(
    monkeypatch,
):
    async def fake_search(
        **kwargs,
    ):
        return make_tool_result(
            classification="confidential"
        )

    async def fake_local_generate(
        *,
        model,
        prompt,
        temperature,
        num_ctx,
        max_output_tokens,
    ):
        return {
            "response": (
                "RESPOSTA_LOCAL"
            ),
            "prompt_eval_count": 20,
            "eval_count": 8,
            "total_duration": (
                100_000_000
            ),
        }

    monkeypatch.setattr(
        service,
        "search_enterprise_knowledge",
        fake_search,
    )

    monkeypatch.setattr(
        generation.ollama_provider,
        "generate",
        fake_local_generate,
    )

    result = asyncio.run(
        run_enterprise_knowledge_agent(
            request=AgentRunRequest(
                message="teste",
                provider="local_fast",
            ),
            organization_id=42,
            principal_id=10,
            question_classification=(
                "public"
            ),
            allowed_classifications={
                "confidential"
            },
        )
    )

    assert (
        result.answer
        == "RESPOSTA_LOCAL"
    )

    assert (
        result.provider
        == "local_fast"
    )

    assert (
        result.effective_classification
        == "confidential"
    )
