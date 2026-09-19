from pydantic import BaseModel, ConfigDict, Field

from app.core.config import ProviderName
from app.schemas import DataClassification


class RagGenerateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    question: str = Field(
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


class PublicRagCitation(BaseModel):
    title: str
    source: str


class PublicRagGenerateResponse(BaseModel):
    answer: str

    provider: ProviderName
    backend: str
    model: str

    effective_classification: DataClassification

    citations: list[PublicRagCitation]

    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    reasoning_tokens: int | None = None

    total_duration_ms: float | None = None

    pricing_tier: str | None = None
    estimated_cost_usd: float | None = None


class RagCitation(BaseModel):
    document_id: int
    title: str
    source: str
    classification: DataClassification
    chunk_index: int
    similarity: float


class RagGenerateResponse(BaseModel):
    answer: str

    provider: ProviderName
    backend: str
    model: str

    effective_classification: DataClassification

    citations: list[RagCitation]

    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    reasoning_tokens: int | None = None

    total_duration_ms: float | None = None

    pricing_tier: str | None = None
    estimated_cost_usd: float | None = None
