import asyncio
from types import SimpleNamespace

import pytest

from app.cli import ingest_document as module


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.delenv("AEL_API_KEY", raising=False)

    with pytest.raises(
        module.IngestCliError,
        match="AEL_API_KEY is not configured",
    ):
        module._read_api_key()


def test_ingest_file_uses_authenticated_context(
    monkeypatch,
    tmp_path,
):
    document = tmp_path / "document.txt"
    document.write_text("conteudo corporativo", encoding="utf-8")
    captured = {}

    async def fake_authenticate(token):
        assert token == "test-token"
        return SimpleNamespace(
            organization_id=10,
            principal_id=20,
            allowed_classifications=frozenset((
                "public",
                "internal",
            )),
        )

    async def fake_ingest(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            document_id=30,
            chunks_inserted=2,
            duplicate=False,
        )

    monkeypatch.setattr(
        module,
        "authenticate_api_key",
        fake_authenticate,
    )
    monkeypatch.setattr(
        module,
        "ingest_document",
        fake_ingest,
    )

    result = asyncio.run(
        module.ingest_file(
            api_key="test-token",
            file_path=document,
            title="Documento",
            source="quickstart",
            classification="internal",
        )
    )

    assert result.document_id == 30
    assert captured["organization_id"] == 10
    assert captured["created_by_principal_id"] == 20
    assert captured["classification"] == "internal"
    assert captured["access_mode"] == "inherited"
    assert captured["text"] == "conteudo corporativo"


def test_ingest_rejects_classification_above_scope(
    monkeypatch,
    tmp_path,
):
    document = tmp_path / "document.txt"
    document.write_text("conteudo", encoding="utf-8")

    async def fake_authenticate(token):
        return SimpleNamespace(
            organization_id=10,
            principal_id=20,
            allowed_classifications=frozenset(("public",)),
        )

    monkeypatch.setattr(
        module,
        "authenticate_api_key",
        fake_authenticate,
    )

    with pytest.raises(
        module.IngestCliError,
        match="exceeds credential scope",
    ):
        asyncio.run(
            module.ingest_file(
                api_key="test-token",
                file_path=document,
                title="Documento",
                source="quickstart",
                classification="internal",
            )
        )


def test_parser_rejects_invalid_classification():
    parser = module.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--file",
                "document.txt",
                "--title",
                "Documento",
                "--classification",
                "secret",
            ]
        )
