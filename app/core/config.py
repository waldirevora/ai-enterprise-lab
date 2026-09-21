from typing import Literal


from pydantic import model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


AppEnvironment = Literal[
    "development",
    "test",
    "production",
]


ProviderName = Literal[
    "local_fast",
    "local_deep",
    "external_deep",
]


_LOCAL_ONLY_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "testserver",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: AppEnvironment = "development"

    allowed_hosts: tuple[str, ...] = (
        "localhost",
        "127.0.0.1",
        "testserver",
    )

    ai_default_organization_slug: str = (
        "lab-default"
    )

    ai_default_provider: ProviderName = (
        "local_fast"
    )

    ollama_base_url: str = (
        "http://127.0.0.1:11434"
    )

    ai_local_fast_model: str = (
        "qwen2.5-coder:3b"
    )

    ai_local_deep_model: str = (
        "qwen2.5-coder:7b-instruct-q3_K_S"
    )

    ai_max_prompt_chars: int = 12000
    ai_max_output_tokens: int = 2048

    ai_embedding_model: str = (
        "qwen3-embedding:0.6b"
    )

    ai_embedding_dimensions: int = 1024

    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str = "ai_enterprise_lab"
    postgres_user: str = "ai_lab"
    postgres_password: str = ""

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    redis_connect_timeout_seconds: float = 1.0
    redis_socket_timeout_seconds: float = 1.0
    redis_readiness_timeout_seconds: float = 3.0

    rate_limit_enabled: bool = True

    rate_limit_public_generate_per_minute: int = 12
    rate_limit_public_generate_burst: int = 3

    rate_limit_public_rag_per_minute: int = 12
    rate_limit_public_rag_burst: int = 3

    rate_limit_auth_preauth_per_minute: int = 30
    rate_limit_auth_preauth_burst: int = 10

    rate_limit_auth_principal_per_minute: int = 30
    rate_limit_auth_principal_burst: int = 5

    external_ai_enabled: bool = False
    external_ai_provider: str = "deepseek"
    external_ai_model: str = "deepseek-flash"

    deepseek_api_key: str = ""
    deepseek_base_url: str = (
        "https://api.deepseek.com"
    )

    deepseek_thinking_enabled: bool = True
    deepseek_reasoning_effort: str = "high"

    deepseek_price_cache_hit_offpeak_per_m: float = (
        0.003
    )

    deepseek_price_cache_miss_offpeak_per_m: float = (
        0.15
    )

    deepseek_price_output_offpeak_per_m: float = (
        0.60
    )

    deepseek_peak_multiplier: float = 2.0


    @model_validator(mode="after")
    def validate_security_configuration(
        self,
    ) -> "Settings":
        if (
            self.external_ai_enabled
            and not self.deepseek_api_key.strip()
        ):
            raise ValueError(
                "DEEPSEEK_API_KEY is required "
                "when external AI is enabled."
            )

        if self.app_env != "production":
            return self

        if not self.rate_limit_enabled:
            raise ValueError(
                "RATE_LIMIT_ENABLED must be true "
                "in production."
            )

        if not self.postgres_password.strip():
            raise ValueError(
                "POSTGRES_PASSWORD is required "
                "in production."
            )

        if (
            self.rate_limit_enabled
            and not self.redis_password.strip()
        ):
            raise ValueError(
                "REDIS_PASSWORD is required "
                "in production when rate limiting "
                "is enabled."
            )

        normalized_hosts = tuple(
            host.strip().lower()
            for host in self.allowed_hosts
            if host.strip()
        )

        if any(
            "*" in host
            for host in normalized_hosts
        ):
            raise ValueError(
                "Production ALLOWED_HOSTS "
                "must not contain wildcards."
            )

        deployment_hosts = tuple(
            host
            for host in normalized_hosts
            if host not in _LOCAL_ONLY_HOSTS
        )

        if not deployment_hosts:
            raise ValueError(
                "Production ALLOWED_HOSTS must "
                "include an explicit deployment host."
            )

        return self


settings = Settings()
