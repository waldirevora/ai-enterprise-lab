import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMPOSE_PATH = (
    ROOT
    / "infra"
    / "compose.prod.yaml"
)

TEMPLATE_PATH = (
    ROOT
    / "infra"
    / ".env.prod.example"
)


SECRET_KEYS = {
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "N8N_DB_PASSWORD",
    "N8N_ENCRYPTION_KEY",
    "DEEPSEEK_API_KEY",
}


def _parse_env_file(
    path: Path,
) -> dict[str, str]:
    result: dict[str, str] = {}

    for raw in path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        key = key.strip()

        assert key not in result, (
            f"Duplicate env key: {key}"
        )

        result[key] = value.strip()

    return result


def _compose_variable_names() -> set[str]:
    text = COMPOSE_PATH.read_text(
        encoding="utf-8"
    )

    return set(
        re.findall(
            r"\$\{([A-Z][A-Z0-9_]*)"
            r"(?::[-?][^}]*)?\}",
            text,
        )
    )


def test_production_env_template_matches_compose_contract():
    template = _parse_env_file(
        TEMPLATE_PATH
    )

    assert set(template) == (
        _compose_variable_names()
    )


def test_production_env_template_keeps_secrets_empty():
    template = _parse_env_file(
        TEMPLATE_PATH
    )

    for key in SECRET_KEYS:
        assert key in template
        assert template[key] == ""


def test_production_compose_requires_explicit_image_tag():
    compose_text = COMPOSE_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "${APP_IMAGE_TAG:?"
        "APP_IMAGE_TAG is required}"
        in compose_text
    )

    template = _parse_env_file(
        TEMPLATE_PATH
    )

    assert template[
        "APP_IMAGE_TAG"
    ] == ""
