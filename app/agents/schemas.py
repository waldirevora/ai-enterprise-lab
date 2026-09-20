from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.config import ProviderName
from app.schemas import DataClassification


AgentToolName = Literal[
    "search_enterprise_knowledge"
]

AgentToolStatus = Literal[
    "completed",
    "failed",
]


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    message: str = Field(
        min_length=1,
        max_length=3000,
    )

    provider: ProviderName | None = None

    external_approved: bool = False

    retrieval_limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    max_context_chunks: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    max_context_characters: int = Field(
        default=8000,
        ge=1,
        le=8000,
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
    )

    num_ctx: int = Field(
        default=4096,
        ge=512,
        le=32768,
    )

    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
    )


class AgentCitation(BaseModel):
    document_id: int

    title: str
    source: str

    classification: DataClassification

    chunk_index: int
    similarity: float


class AgentToolTrace(BaseModel):
    name: AgentToolName

    status: AgentToolStatus

    chunks_used: int = Field(
        ge=0,
    )

    characters_used: int = Field(
        ge=0,
    )


class AgentRunResponse(BaseModel):
    answer: str

    provider: ProviderName

    backend: str
    model: str

    effective_classification: (
        DataClassification
    )

    citations: list[AgentCitation]

    tool_trace: list[AgentToolTrace]

    steps_executed: int = Field(
        ge=1,
        le=3,
    )

    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    reasoning_tokens: int | None = None

    total_duration_ms: float | None = None

    pricing_tier: str | None = None
    estimated_cost_usd: float | None = None
