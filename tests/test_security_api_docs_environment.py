import pytest

import app.main as main_module


@pytest.mark.parametrize(
    "app_env",
    [
        "development",
        "test",
    ],
)
def test_api_docs_are_enabled_outside_production(
    monkeypatch,
    app_env,
):
    monkeypatch.setattr(
        main_module.settings,
        "app_env",
        app_env,
    )

    application = (
        main_module._build_fastapi_app()
    )

    assert (
        application.docs_url
        == "/docs"
    )

    assert (
        application.redoc_url
        == "/redoc"
    )

    assert (
        application.openapi_url
        == "/openapi.json"
    )


def test_api_docs_are_disabled_in_production(
    monkeypatch,
):
    monkeypatch.setattr(
        main_module.settings,
        "app_env",
        "production",
    )

    application = (
        main_module._build_fastapi_app()
    )

    assert application.docs_url is None
    assert application.redoc_url is None
    assert application.openapi_url is None
