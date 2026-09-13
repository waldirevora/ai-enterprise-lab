from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal[
    "local_fast",
    "local_deep",
    "external_deep",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_default_provider: ProviderName = "local_fast"

    ollama_base_url: str = "http://127.0.0.1:11434"

    ai_local_fast_model: str = "qwen2.5-coder:3b"
    ai_local_deep_model: str = "qwen2.5-coder:7b-instruct-q3_K_S"

    ai_max_prompt_chars: int = 12000
    ai_max_output_tokens: int = 2048

    external_ai_enabled: bool = False
    external_ai_provider: str = "deepseek"
    external_ai_model: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_thinking_enabled: bool = True
    deepseek_reasoning_effort: str = "high"

    deepseek_price_cache_hit_offpeak_per_m: float = 0.022
    deepseek_price_cache_miss_offpeak_per_m: float = 0.66
    deepseek_price_output_offpeak_per_m: float = 1.98
    deepseek_peak_multiplier: float = 2.0


settings = Settings()