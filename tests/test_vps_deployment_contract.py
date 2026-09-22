from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RUNBOOK = (
    ROOT
    / "infra"
    / "VPS_DEPLOYMENT.md"
)

PREFLIGHT = (
    ROOT
    / "infra"
    / "scripts"
    / "preflight_vps.sh"
)


def test_vps_runbook_preserves_deployment_order():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    postgres = text.index(
        "## Start PostgreSQL"
    )

    migration = text.index(
        "## Database migration"
    )

    stack = text.index(
        "## Start application stack"
    )

    assert postgres < migration < stack


def test_vps_runbook_requires_explicit_migration():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    assert (
        "run --rm --no-deps app"
        in text
    )

    assert (
        "python -m app.db.migrations apply"
        in text
    )


def test_vps_runbook_contains_acceptance_checks():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    for marker in (
        "/health",
        "/ready",
        "HTTPS certificate valid",
        "n8n loopback-only",
        "migration status clean",
    ):
        assert marker in text


def test_vps_runbook_contains_backup_and_rollback():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    assert (
        "backup_postgres.sh"
        in text
    )

    assert (
        "previous known-good immutable release tag"
        in text
    )

    assert (
        "ROLLBACK_RECOVERY.md"
        in text
    )


def test_preflight_checks_sensitive_env_contract():
    text = PREFLIGHT.read_text(
        encoding="utf-8"
    )

    assert (
        'ENV_MODE" = "600'
        in text
    )

    assert (
        "outside repository"
        in text
    )

    assert (
        "config \\\n    --quiet"
        in text
    )


def test_preflight_rejects_common_mutable_tags():
    text = PREFLIGHT.read_text(
        encoding="utf-8"
    )

    for tag in (
        "latest",
        "prod",
        "production",
        "main",
        "master",
    ):
        assert tag in text


def test_production_redis_runs_as_non_root_image_user():
    import yaml

    compose = yaml.safe_load(
        (
            ROOT
            / "infra"
            / "compose.prod.yaml"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        compose["services"]["redis"]["user"]
        == "redis"
    )


def test_post_start_migration_status_uses_exec():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    section = text.split(
        "## Migration status",
        1,
    )[1].split(
        "## Logs",
        1,
    )[0]

    assert (
        "exec -T app"
        in section
    )

    assert (
        "python -m app.db.migrations status"
        in section
    )

    assert (
        "run --rm --no-deps app"
        not in section
    )


def test_pre_start_migration_still_uses_one_off_run():
    text = RUNBOOK.read_text(
        encoding="utf-8"
    )

    section = text.split(
        "## Database migration",
        1,
    )[1].split(
        "## Start application stack",
        1,
    )[0]

    assert (
        "run --rm --no-deps app"
        in section
    )

    assert (
        "python -m app.db.migrations apply"
        in section
    )


def test_dockerfile_disables_uvicorn_access_log():
    dockerfile = (
        ROOT / "Dockerfile"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        '"--no-access-log"'
        in dockerfile
    )


def test_production_compose_disables_uvicorn_access_log():
    import yaml

    compose = yaml.safe_load(
        (
            ROOT
            / "infra"
            / "compose.prod.yaml"
        ).read_text(
            encoding="utf-8"
        )
    )

    command = (
        compose["services"]["app"]["command"]
    )

    assert (
        "--no-access-log"
        in command
    )

    assert (
        command.count(
            "--no-access-log"
        )
        == 1
    )


def test_readme_uvicorn_commands_disable_access_log():
    for filename in (
        "README.md",
        "README_EN.md",
    ):
        text = (
            ROOT / filename
        ).read_text(
            encoding="utf-8"
        )

        commands = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith(
                "uvicorn app.main:app"
            )
        ]

        assert commands

        assert all(
            "--no-access-log"
            in command
            for command in commands
        )
