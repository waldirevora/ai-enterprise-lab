from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import ProviderName


DataClassification = Literal[
    "public",
    "internal",
    "confidential",
]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    provider: ProviderName | None = None

    data_classification: DataClassification = "internal"
    external_approved: bool = False

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


class GenerateResponse(BaseModel):
    provider: ProviderName
    backend: str
    model: str
    response: str

    prompt_tokens: int | None = None
    generated_tokens: int | None = None

    reasoning_tokens: int | None = None
    prompt_cache_hit_tokens: int | None = None
    prompt_cache_miss_tokens: int | None = None

    total_duration_ms: float | None = None

    pricing_tier: str | None = None
    estimated_cost_usd: float | None = None