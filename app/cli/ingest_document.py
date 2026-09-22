import argparse
import asyncio
import os
import sys
from pathlib import Path

from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
    authenticate_api_key,
)
from app.rag.ingestion import (
    RagIngestionError,
    ingest_document,
)


class IngestCliError(Exception):
    pass


def _read_api_key() -> str:
    token = os.environ.get("AEL_API_KEY", "").strip()
    if not token:
        raise IngestCliError(
            "AEL_API_KEY is not configured."
        )
    return token


def _read_utf8_file(path: Path) -> str:
    if not path.is_file():
        raise IngestCliError(
            f"Document file was not found: {path}"
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise IngestCliError(
            "Document must be valid UTF-8 text."
        ) from exc


async def ingest_file(
    *,
    api_key: str,
    file_path: Path,
    title: str,
    source: str,
    classification: str,
    source_uri: str | None = None,
):
    title = title.strip()
    source = source.strip()

    if not title:
        raise IngestCliError("Document title cannot be empty.")
    if not source:
        raise IngestCliError("Document source cannot be empty.")

    context = await authenticate_api_key(api_key)

    if classification not in context.allowed_classifications:
        raise IngestCliError(
            "Requested classification exceeds credential scope."
        )

    text = _read_utf8_file(file_path)

    return await ingest_document(
        organization_id=context.organization_id,
        created_by_principal_id=context.principal_id,
        title=title,
        source=source,
        text=text,
        classification=classification,
        access_mode="inherited",
        source_uri=source_uri,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest a UTF-8 document into AI Enterprise Lab RAG."
        )
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--source")
    parser.add_argument(
        "--classification",
        choices=("public", "internal", "confidential"),
        default="internal",
    )
    parser.add_argument("--source-uri")
    return parser


async def _run(args: argparse.Namespace) -> int:
    api_key = _read_api_key()

    source = (
        args.source.strip()
        if args.source
        else f"file:{args.file.name}"
    )

    result = await ingest_file(
        api_key=api_key,
        file_path=args.file,
        title=args.title,
        source=source,
        classification=args.classification,
        source_uri=args.source_uri,
    )

    print("INGEST_DOCUMENT=PASS")
    print(f"document_id={result.document_id}")
    print(f"chunks_inserted={result.chunks_inserted}")
    print(f"duplicate={str(result.duplicate).lower()}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(_run(args))
    except (
        IngestCliError,
        AuthenticationError,
        AuthenticationUnavailableError,
        RagIngestionError,
        OSError,
    ) as exc:
        print(f"INGEST_DOCUMENT=FAIL error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
