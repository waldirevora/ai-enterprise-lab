from app.core.config import ProviderName, settings


def get_provider_catalog() -> dict:
    return {
        "default": settings.ai_default_provider,
        "providers": {
            "local_fast": {
                "type": "local",
                "backend": "ollama",
                "model": settings.ai_local_fast_model,
                "enabled": True,
            },
            "local_deep": {
                "type": "local",
                "backend": "ollama",
                "model": settings.ai_local_deep_model,
                "enabled": True,
            },
            "external_deep": {
                "type": "external",
                "backend": settings.external_ai_provider,
                "model": settings.external_ai_model,
                "enabled": settings.external_ai_enabled,
            },
        },
    }


def get_public_provider_catalog() -> dict:
    catalog = get_provider_catalog()

    return {
        "default": catalog["default"],
        "providers": {
            provider_name: {
                "enabled": provider_config["enabled"],
            }
            for (
                provider_name,
                provider_config,
            ) in catalog["providers"].items()
        },
    }


def provider_exists(provider: ProviderName) -> bool:
    return provider in get_provider_catalog()["providers"]
